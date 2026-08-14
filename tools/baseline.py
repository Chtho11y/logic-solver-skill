"""Compile + accept + free-solve baseline for every implemented key.

Records constraint counts, SAT statuses and a model fingerprint so later
refactors (P1–P6) can be checked against a frozen snapshot.

    python -u -m tools.baseline
    python -u -m tools.baseline --keys nurikabe hitori
    python -u -m tools.baseline --resume
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from puzzle.dsl.values import sort_points  # noqa: E402
from puzzle.grid import Grid  # noqa: E402
from puzzle.models import VarType, point_key  # noqa: E402
from puzzle.runner import solve_instance  # noqa: E402
from puzzle.spec import (  # noqa: E402
    Instance,
    PuzzleSpec,
    build_grid,
    build_params,
    build_regions,
    build_variables,
    implemented_keys,
    load_sample,
    load_spec,
    make_loader,
)
from puzzle.dsl import STATUS_ERROR, compile_only  # noqa: E402
from tests.puzzles import instance_payload, load_fixture  # noqa: E402
from tools.check import synthetic_instance  # noqa: E402

CASES_DIR = ROOT / "tests" / "cases"
BASELINE_DIR = ROOT / "docs" / "baseline"


def git_sha() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        sha = (proc.stdout or "").strip()
        if sha:
            return sha
    except OSError:
        pass
    return "unknown"


def z3_version() -> str:
    try:
        import z3

        return z3.get_version_string()
    except Exception:
        return "unavailable"


def unencoded_clues(key: str) -> list[str]:
    path = ROOT / "impls" / f"{key}.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("unencodedClues") or []
    return [str(item) for item in raw]


def load_case(key: str) -> dict[str, Any] | None:
    path = CASES_DIR / f"{key}.json"
    if not path.is_file():
        return None
    data = load_fixture(path)
    cases = data.get("cases") or []
    return cases[0] if cases else None


def instance_for(key: str) -> tuple[Instance | None, dict[str, Any] | None, str]:
    """Prefer a fixture (has an answer), then the shipped sample, else nothing."""

    case = load_case(key)
    if case is not None:
        return Instance.from_json(instance_payload(key, case, with_answer=False)), case, "fixture"
    sample = load_sample(key)
    if sample is not None:
        return sample, None, "sample"
    return None, None, "none"


def model_fingerprint(
    spec: PuzzleSpec,
    instance: Instance,
    values: dict[str, dict[str, int]] | None,
) -> str:
    """SHA-256[:16] of NORMAL/CC assignments in ``sort_points`` order."""

    if not values:
        return ""
    grid = Grid(instance.rows, instance.cols)
    hasher = hashlib.sha256()
    for var in spec.variables:
        if var.var_type not in (VarType.NORMAL, VarType.CC):
            continue
        table = values.get(var.name) or {}
        hasher.update(f"#{var.name}\n".encode())
        for point in sort_points(grid.points(var.kind)):
            key = point_key(point)
            hasher.update(f"{key}={table.get(key, '')}\n".encode())
    return hasher.hexdigest()[:16]


def pin_assignment(instance: Instance, spec: PuzzleSpec, values: dict[str, dict[str, int]]) -> Instance:
    """Copy NORMAL/CC model values into clues so the assignment is fully given."""

    clues = {name: dict(layer) for name, layer in instance.clues.items()}
    for var in spec.variables:
        if var.var_type is VarType.CONSTANT:
            continue
        if var.name not in values:
            continue
        clues[var.name] = {str(k): int(v) for k, v in values[var.name].items()}
    return Instance(
        puzzle=instance.puzzle,
        rows=instance.rows,
        cols=instance.cols,
        clues=clues,
        regions=dict(instance.regions),
        params=dict(instance.params),
        title=instance.title,
    )


def _output_var_names(spec: PuzzleSpec) -> list[str]:
    preferred = [layer.var for layer in spec.layers if layer.role == "output" and layer.var]
    rest = [
        var.name
        for var in spec.variables
        if var.var_type in (VarType.NORMAL, VarType.CC)
    ]
    seen: set[str] = set()
    names: list[str] = []
    for name in preferred + rest:
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def iter_corruptions(
    spec: PuzzleSpec,
    values: dict[str, dict[str, int]],
    limit: int = 40,
):
    """Yield one-cell flips of NORMAL/CC output variables."""

    yielded = 0
    for name in _output_var_names(spec):
        var = spec.var_spec(name)
        if var is None or var.var_type not in (VarType.NORMAL, VarType.CC):
            continue
        table = values.get(name) or {}
        if not table:
            continue
        if var.var_type is VarType.CC:
            ids = sorted({int(v) for v in table.values()})
        else:
            ids = []
        lo, hi = var.domain if var.domain is not None else (0, 1)
        for key in sorted(table):
            current = int(table[key])
            if var.var_type is VarType.CC:
                others = [i for i in ids if i != current]
                alt = others[0] if others else current + 1
            else:
                alt = lo if current != lo else lo + 1
                if alt > hi or alt == current:
                    continue
            flipped = {n: dict(layer) for n, layer in values.items()}
            flipped[name] = dict(table)
            flipped[name][key] = alt
            yield flipped, name, key, current, alt
            yielded += 1
            if yielded >= limit:
                return


def corrupt_assignment(
    spec: PuzzleSpec,
    values: dict[str, dict[str, int]],
) -> tuple[dict[str, dict[str, int]], str, str, int, int] | None:
    """Flip one NORMAL/CC output cell to a different in-domain value."""

    return next(iter_corruptions(spec, values, limit=1), None)


def _status(result: dict[str, Any], *, timed_out: bool) -> str:
    status = result.get("status") or "error"
    if status == "unknown" and timed_out:
        return "timeout"
    return status


def _compile(spec: PuzzleSpec, instance: Instance) -> tuple[str, int | None, str]:
    grid = build_grid(instance)
    result = compile_only(
        grid,
        build_variables(spec, instance, grid),
        build_regions(spec, instance, grid),
        spec.source,
        build_params(spec, instance),
        make_loader(),
    )
    if result.status == STATUS_ERROR:
        return "error", None, result.message
    return "ok", result.constraint_count, ""


def measure_key(key: str, timeout_ms: int) -> dict[str, Any]:
    row: dict[str, Any] = {
        "key": key,
        "constraints": None,
        "compile": "skip",
        "accept": "skip",
        "free-solve": "skip",
        "ms": None,
        "fingerprint": "",
        "source": "none",
        "unencodedClues": unencoded_clues(key),
        "message": "",
    }
    try:
        spec = load_spec(key)
    except Exception as exc:
        row["compile"] = "error"
        row["message"] = str(exc)
        return row
    if not spec.source.strip():
        row["compile"] = "error"
        row["message"] = "no DSL program"
        return row

    instance, case, source = instance_for(key)
    row["source"] = source
    compile_inst = instance if instance is not None else synthetic_instance(key)
    compile_status, count, compile_msg = _compile(spec, compile_inst)
    row["compile"] = compile_status
    row["constraints"] = count
    if compile_status != "ok":
        row["message"] = compile_msg
        return row

    if case is not None and case.get("answer"):
        pinned = Instance.from_json(instance_payload(key, case, with_answer=True))
        started = time.perf_counter()
        result = solve_instance(spec, pinned, timeout_ms=timeout_ms)
        elapsed = time.perf_counter() - started
        row["accept"] = _status(result, timed_out=elapsed * 1000 >= timeout_ms * 0.95)
        if row["accept"] not in ("sat", "unsat", "timeout", "unknown"):
            row["message"] = (result.get("message") or "")[:200]
    elif instance is None:
        return row

    if instance is None:
        return row
    started = time.perf_counter()
    result = solve_instance(spec, instance, timeout_ms=timeout_ms)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    row["ms"] = elapsed_ms
    row["free-solve"] = _status(result, timed_out=elapsed_ms >= timeout_ms * 0.95)
    if row["free-solve"] == "sat":
        row["fingerprint"] = model_fingerprint(spec, instance, result.get("values"))
    elif not row["message"]:
        row["message"] = (result.get("message") or "")[:200]
    return row


def _load_existing(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="record a compile/accept/solve baseline")
    parser.add_argument("keys", nargs="*")
    parser.add_argument("--timeout", type=int, default=60000, help="z3 timeout in ms")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--resume", action="store_true", help="skip keys already in --out")
    args = parser.parse_args(argv)

    sha = git_sha()
    out = args.out or (BASELINE_DIR / f"{sha}.json")
    keys = args.keys or implemented_keys()
    payload = _load_existing(out) if args.resume else {}
    by_key = {row["key"]: row for row in payload.get("keys", []) if "key" in row}

    payload.update(
        {
            "sha": payload.get("sha") or sha,
            "z3": z3_version(),
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "timeout_ms": args.timeout,
        }
    )

    print(f"baseline {sha}  z3={payload['z3']}  timeout={args.timeout}ms  out={out}", flush=True)
    for index, key in enumerate(keys, 1):
        if args.resume and key in by_key:
            print(f"[{index}/{len(keys)}] skip {key}", flush=True)
            continue
        started = time.perf_counter()
        row = measure_key(key, args.timeout)
        by_key[key] = row
        payload["keys"] = [by_key[k] for k in keys if k in by_key]
        _write(out, payload)
        elapsed = time.perf_counter() - started
        print(
            f"[{index}/{len(keys)}] {key:16} compile={row['compile']:5} "
            f"accept={row['accept']:7} free={row['free-solve']:7} "
            f"n={str(row['constraints']):>6} {elapsed:6.1f}s  {row['fingerprint']}",
            flush=True,
        )
        if row["message"] and row["compile"] == "error":
            print(f"         {row['message'][:120]}", flush=True)

    payload["keys"] = [by_key[k] for k in keys if k in by_key]
    _write(out, payload)
    print(f"\nwrote {len(payload['keys'])} key(s) → {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
