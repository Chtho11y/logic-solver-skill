"""Uniqueness sweep for implemented keys (META_SOLVE_PLAN PM-4).

Appends a ``meta:`` uniqueness check and classifies each instance as unique,
multiple, unsat, timeout, or error. Partial encodings (nonempty
``unencodedClues``) are skipped — they are expected to admit extra solutions.

    python -u -m tools.uniqueness
    python -u -m tools.uniqueness --keys sudoku yajilin
    python -u -m tools.uniqueness --resume
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from puzzle.models import VarType  # noqa: E402
from puzzle.runner import solve_instance  # noqa: E402
from puzzle.spec import PuzzleSpec, implemented_keys, load_spec  # noqa: E402
from tools.baseline import (  # noqa: E402
    BASELINE_DIR,
    _output_var_names,
    git_sha,
    instance_for,
    unencoded_clues,
    z3_version,
)

REPORT_PATH = BASELINE_DIR / "uniqueness.json"


def uniqueness_program(source: str, names: list[str]) -> str:
    """Append a top-level uniqueness check over ``names``."""

    if not names:
        raise ValueError("uniqueness_program needs at least one variable")
    args = ", ".join(names)
    suffix = (
        "\nimport \"meta\"\n"
        "meta:\n"
        f"    unique_over({args})\n"
        "    let s1 = solve()\n"
        '    require(s1.sat, "UNSAT: encoding rejects the intended answer")\n'
        "    scope:\n"
        "        exclude(s1)\n"
        "        let s2 = solve()\n"
        '    require(not s2.sat, "MULTIPLE: encoding admits more than one solution")\n'
    )
    return source.rstrip() + suffix


def classify_result(payload: dict[str, Any]) -> tuple[str, str]:
    """Map a ``solve_instance`` payload to (status, message)."""

    status = payload.get("status") or ""
    message = str(payload.get("message") or "")
    if status == "sat":
        return "unique", message
    if status == "unknown":
        return "timeout", message
    if status == "unsat":
        return "unsat", message
    if "MULTIPLE" in message:
        return "multiple", message
    if "UNSAT" in message:
        return "unsat", message
    if "unknown" in message.lower() or "timeout" in message.lower():
        return "timeout", message
    return "error", message


def check_uniqueness(
    spec: PuzzleSpec,
    instance,
    timeout_ms: int = 30000,
    names: list[str] | None = None,
) -> dict[str, Any]:
    """Run the uniqueness template; return status / message / elapsed ms."""

    vars_ = names if names is not None else _output_var_names(spec)
    decisive = [
        name
        for name in vars_
        if (spec.var_spec(name) is not None and spec.var_spec(name).var_type in (VarType.NORMAL, VarType.CC))
    ]
    if not decisive:
        return {"status": "error", "message": "no NORMAL/CC output variables", "ms": 0}
    source = uniqueness_program(spec.source, decisive)
    started = time.perf_counter()
    payload = solve_instance(
        spec,
        instance,
        timeout_ms=timeout_ms,
        source=source,
        run_meta=True,
    )
    elapsed = int((time.perf_counter() - started) * 1000)
    status, message = classify_result(payload)
    return {"status": status, "message": message, "ms": elapsed, "vars": decisive}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="uniqueness sweep")
    parser.add_argument("--keys", nargs="*", default=None)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)

    keys = list(args.keys) if args.keys else implemented_keys()
    previous: dict[str, dict[str, Any]] = {}
    if args.resume and args.out.is_file():
        previous = {
            row["key"]: row
            for row in json.loads(args.out.read_text(encoding="utf-8")).get("keys", [])
        }

    rows: list[dict[str, Any]] = []
    for key in keys:
        if key in previous and previous[key].get("status") not in {"", None}:
            rows.append(previous[key])
            print(f"skip {key} (resume {previous[key].get('status')})", flush=True)
            continue
        spec = load_spec(key)
        instance, _case, source_kind = instance_for(key)
        skipped = unencoded_clues(key)
        row: dict[str, Any] = {
            "key": key,
            "status": "skip",
            "message": "",
            "ms": 0,
            "source": source_kind,
            "unencodedClues": skipped,
            "vars": _output_var_names(spec),
        }
        if instance is None:
            row["status"] = "error"
            row["message"] = "no sample or fixture"
        elif skipped:
            row["message"] = f"unencodedClues: {','.join(skipped)}"
        else:
            result = check_uniqueness(spec, instance, timeout_ms=args.timeout_ms)
            row.update(result)
        rows.append(row)
        print(f"{row['status']:10} {key:16} {row['ms']:6}ms  {row['message'][:80]}", flush=True)

        payload = {
            "sha": git_sha(),
            "z3": z3_version(),
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "timeout_ms": args.timeout_ms,
            "keys": rows,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    print("\n" + " ".join(f"{name}={n}" for name, n in sorted(counts.items())))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
