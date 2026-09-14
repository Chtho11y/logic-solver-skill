"""Compare Z3 vs cspuz_core compile/solve time for P0–P2 encodings.

    python -m tools.bench_backends
    python -m tools.bench_backends --samples
    python -m tools.bench_backends --size 12 --timeout 60000
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from puzzle.backends import backend_info  # noqa: E402
from puzzle.dsl.compiler import compile_source  # noqa: E402
from puzzle.dsl.solver import solve  # noqa: E402
from puzzle.grid import Grid  # noqa: E402
from puzzle.models import PointKind, Variable  # noqa: E402
from puzzle.runner import solve_instance  # noqa: E402
from puzzle.spec import implemented_keys, load_sample, load_spec  # noqa: E402


MICROS = (
    ("connected", "cell", "connected(x, 1)\n"),
    ("connected8", "cell", "connected8(x, 1)\n"),
    ("island_rule", "cell", "island_rule(x)\n"),
    ("wall_rule", "cell", "wall_rule(x)\n"),
    ("loop", "edge", "loop(e)\n"),
    ("cloop", "edge", "cloop(e)\n"),
    ("cc_size", "cell", "let sz = cc_size(x)\nfor p in cells():\n    at(sz, p) >= 1\n"),
    ("groups_of_size", "cell", "let sz = cc_size(x)\nfor p in cells():\n    at(x, p) == 1 => at(sz, p) == 4\n"),
)

SAMPLE_FOCUS = (
    "hitori",
    "heyawake",
    "nurikabe",
    "aqre",
    "slither",
    "masyu",
    "simpleloop",
    "yajilin",
    "tetrochain",
    "yinyang",
)


def _available(name: str) -> bool:
    return bool(backend_info(name).available)


def _grid_vars(kind: str, size: int):
    grid = Grid(size, size)
    if kind == "edge":
        return grid, [Variable("e", kind=PointKind.EDGE, domain=(0, 1))]
    return grid, [Variable("x", domain=(0, 1))]


def _timed(fn):
    started = time.perf_counter()
    result = fn()
    return time.perf_counter() - started, result


def _fmt(seconds: float | None) -> str:
    if seconds is None:
        return "n/a"
    if seconds < 0.001:
        return f"{seconds * 1e6:.0f}us"
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    return f"{seconds:.2f}s"


def _ratio(z3: float | None, core: float | None) -> str:
    if z3 is None or core is None or core <= 0:
        return "n/a"
    return f"{z3 / core:.1f}x"


def bench_micro(size: int, backends: list[str], timeout_ms: int | None) -> list[dict]:
    rows = []
    for name, kind, source in MICROS:
        grid, variables = _grid_vars(kind, size)
        row = {"name": f"{name} {size}x{size}"}
        for backend in backends:
            program = f"use {backend}\n{source}"
            compile_s, compiled = _timed(
                lambda program=program: compile_source(program, grid, variables, [])
            )
            solve_timeout = None if backend != "z3" else timeout_ms
            solve_s, result = _timed(
                lambda program=program, backend=backend, solve_timeout=solve_timeout: solve(
                    grid,
                    variables,
                    [],
                    program,
                    backend=backend,
                    timeout_ms=solve_timeout,
                )
            )
            row[f"{backend}_compile"] = compile_s
            row[f"{backend}_solve"] = solve_s
            row[f"{backend}_status"] = result.status
            row[f"{backend}_constraints"] = compiled and len(compiled.constraints)
        rows.append(row)
    return rows


def bench_samples(keys: list[str], backends: list[str], timeout_ms: int) -> list[dict]:
    rows = []
    for key in keys:
        instance = load_sample(key)
        if instance is None:
            continue
        spec = load_spec(key)
        row = {"name": key, "size": f"{instance.rows}x{instance.cols}"}
        for backend in backends:
            solve_timeout = timeout_ms if backend == "z3" else None
            elapsed, result = _timed(
                lambda backend=backend, solve_timeout=solve_timeout: solve_instance(
                    spec, instance, backend=backend, timeout_ms=solve_timeout
                )
            )
            row[f"{backend}_solve"] = elapsed
            row[f"{backend}_status"] = result.get("status")
        rows.append(row)
    return rows


def _print_micro(rows: list[dict], backends: list[str]) -> None:
    print("\n## micro (compile + find_answer)")
    header = ["encoding"]
    for backend in backends:
        header.extend([f"{backend} compile", f"{backend} solve", "status"])
    if "z3" in backends and "cspuz_core" in backends:
        header.append("solve Z3/core")
    print(" | ".join(header))
    print(" | ".join("---" for _ in header))
    for row in rows:
        cells = [row["name"]]
        for backend in backends:
            cells.append(_fmt(row.get(f"{backend}_compile")))
            cells.append(_fmt(row.get(f"{backend}_solve")))
            cells.append(str(row.get(f"{backend}_status") or ""))
        if "z3" in backends and "cspuz_core" in backends:
            cells.append(_ratio(row.get("z3_solve"), row.get("cspuz_core_solve")))
        print(" | ".join(cells))


def _print_samples(rows: list[dict], backends: list[str]) -> None:
    print("\n## samples (find_answer)")
    header = ["puzzle", "size"]
    for backend in backends:
        header.extend([f"{backend}", "status"])
    if "z3" in backends and "cspuz_core" in backends:
        header.append("Z3/core")
    print(" | ".join(header))
    print(" | ".join("---" for _ in header))
    z3_total = 0.0
    core_total = 0.0
    compared = 0
    for row in rows:
        cells = [row["name"], row.get("size", "")]
        for backend in backends:
            cells.append(_fmt(row.get(f"{backend}_solve")))
            cells.append(str(row.get(f"{backend}_status") or ""))
        if "z3" in backends and "cspuz_core" in backends:
            cells.append(_ratio(row.get("z3_solve"), row.get("cspuz_core_solve")))
            if row.get("z3_solve") is not None and row.get("cspuz_core_solve") is not None:
                z3_total += row["z3_solve"]
                core_total += row["cspuz_core_solve"]
                compared += 1
        print(" | ".join(cells))
    if compared:
        print(
            f"\n{compared} samples: Z3 {_fmt(z3_total)} vs cspuz_core "
            f"{_fmt(core_total)} ({_ratio(z3_total, core_total)})"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Z3 vs cspuz_core benchmark")
    parser.add_argument("--size", type=int, default=12)
    parser.add_argument("--timeout", type=int, default=60000)
    parser.add_argument("--samples", action="store_true", help="also run impls/samples")
    parser.add_argument("--all-samples", action="store_true")
    parser.add_argument("keys", nargs="*")
    args = parser.parse_args(argv)

    backends = [name for name in ("z3", "cspuz_core") if _available(name)]
    print("backends:", ", ".join(backends) or "(none)")
    if "cspuz_core" not in backends:
        print("cspuz_core is not installed; native timings will be skipped")
    if "z3" not in backends:
        print("Z3 is not installed")
        return 1

    _print_micro(bench_micro(args.size, backends, args.timeout), backends)
    if args.size != 8:
        _print_micro(bench_micro(8, backends, args.timeout), backends)

    if args.all_samples:
        keys = implemented_keys()
        _print_samples(bench_samples(keys, backends, args.timeout), backends)
    elif args.samples or args.keys:
        keys = args.keys or [key for key in SAMPLE_FOCUS if key in set(implemented_keys())]
        _print_samples(bench_samples(keys, backends, args.timeout), backends)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
