"""Validate every bundled implementation.

* ``compile`` — parse + lower each ``impls/*.dsl`` against a synthetic board,
  which catches syntax errors, unknown names and shape mistakes fast.
* ``solve``   — run the sample instances in ``impls/samples/`` and report the
  status (used as the regression suite for the solvers).

    python -m tools.check compile
    python -m tools.check solve [key ...]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from puzzle.dsl import STATUS_ERROR, compile_only  # noqa: E402
from puzzle.models import point_key  # noqa: E402
from puzzle.runner import solve_instance  # noqa: E402
from puzzle.spec import (  # noqa: E402
    Instance,
    build_grid,
    build_params,
    build_regions,
    build_variables,
    implemented_keys,
    load_sample,
    load_spec,
    make_loader,
)


def synthetic_instance(key: str, size: int = 6) -> Instance:
    """A small dummy board: 2x2 block regions, dense constants filled with 1."""

    spec = load_spec(key)
    rows = cols = size
    regions: dict[str, int] = {}
    if spec.uses_regions:
        per_row = (cols + 1) // 2
        for r in range(rows):
            for c in range(cols):
                regions[f"{r},{c}"] = (r // 2) * per_row + (c // 2)
    clues: dict[str, dict[str, int]] = {}
    for var_spec in spec.variables:
        if var_spec.dense:
            clues[var_spec.name] = {
                f"{r},{c}": 1 for r in range(rows) for c in range(cols)
            }
    params: dict = {"stars": 1}
    for side, count in (("top", cols), ("bottom", cols), ("left", rows), ("right", rows)):
        params[side] = [-1] * count
    return Instance(puzzle=key, rows=rows, cols=cols, clues=clues, regions=regions, params=params)


def check_compile(keys: list[str]) -> int:
    failures = 0
    for key in keys:
        spec = load_spec(key)
        instance = synthetic_instance(key)
        grid = build_grid(instance)
        started = time.perf_counter()
        result = compile_only(
            grid,
            build_variables(spec, instance, grid),
            build_regions(spec, instance, grid),
            spec.source,
            build_params(spec, instance),
            make_loader(),
        )
        elapsed = time.perf_counter() - started
        if result.status == STATUS_ERROR:
            failures += 1
            print(f"FAIL {key:14} {result.message}")
        else:
            print(f"ok   {key:14} {result.constraint_count:7} constraints  {elapsed:5.2f}s")
    print(f"\n{len(keys) - failures}/{len(keys)} compiled")
    return 1 if failures else 0


def check_solve(keys: list[str], timeout_ms: int) -> int:
    failures = 0
    tested = 0
    for key in keys:
        instance = load_sample(key)
        if instance is None:
            continue
        tested += 1
        spec = load_spec(key)
        started = time.perf_counter()
        result = solve_instance(spec, instance, timeout_ms=timeout_ms)
        elapsed = time.perf_counter() - started
        status = result["status"]
        mark = "ok  " if status == "sat" else "FAIL"
        if status != "sat":
            failures += 1
        print(f"{mark} {key:14} {status:8} {elapsed:5.2f}s  {result.get('message', '')[:60]}")
        if status == "sat" and instance.rows <= 16:
            print(render(spec, instance, result))
    print(f"\n{tested - failures}/{tested} samples solved")
    return 1 if failures else 0


def render(spec, instance: Instance, result: dict) -> str:
    """A rough text picture of the first cell-shaped output layer."""

    values = result.get("values", {})
    kinds = result.get("kinds", {})
    layer = next(
        (l for l in spec.layers if l.role == "output" and l.target == "cell" and l.var), None
    )
    if layer is None or layer.var not in values:
        return ""
    data = values[layer.var]
    glyphs = {0: "·", 1: "#"} if layer.element in ("shade", "circle", "star") else {}
    lines = []
    for r in range(instance.rows):
        row = []
        for c in range(instance.cols):
            value = data.get(point_key((r, c)))
            row.append(glyphs.get(value, str(value)[-1] if value is not None else " "))
        lines.append("  " + " ".join(row))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="validate puzzle implementations")
    parser.add_argument("mode", choices=("compile", "solve"))
    parser.add_argument("keys", nargs="*")
    parser.add_argument("--timeout", type=int, default=120000)
    args = parser.parse_args(argv)
    keys = args.keys or implemented_keys()
    if args.mode == "compile":
        return check_compile(keys)
    return check_solve(keys, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
