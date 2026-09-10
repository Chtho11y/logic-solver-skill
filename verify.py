"""Verification harness for newly authored rules.

Three checks per rule:
  1. compile   — DSL type-checks against a synthetic board.
  2. solve     — the shipped sample is satisfiable.
  3. bite      — every declared CONSTANT clue variable actually changes the
                 constraint set when given a value. This catches dead code such
                 as calling a pure helper and discarding its result.

    python verify.py <key> [<key> ...]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from puzzle.dsl import compile_only
from puzzle.spec import (build_grid, build_params, build_regions, build_variables,
                         load_sample, load_spec, make_loader, Instance)
from puzzle.runner import solve_instance


def _count(spec, instance):
    grid = build_grid(instance)
    r = compile_only(grid, build_variables(spec, instance, grid),
                     build_regions(spec, instance, grid), spec.source,
                     build_params(spec, instance), make_loader())
    if r.status == "error":
        return None, r.message
    return r.constraint_count, ""


def check(key, backend="auto"):
    import json
    spec = load_spec(key)
    raw = json.loads((Path(__file__).resolve().parent / "impls" / f"{key}.json")
                     .read_text(encoding="utf-8"))
    expected_dead = set(raw.get("unencodedClues", []))
    sm = load_sample(key)
    out = []

    # 1. compile + 2. solve the shipped sample
    n0, err = _count(spec, sm)
    if n0 is None:
        return [f"FAIL {key:16} compile: {err}"]
    res = solve_instance(spec, sm, backend=backend, timeout_ms=60000)
    if res["status"] != "sat":
        return [f"FAIL {key:16} solve: {res['status']} {res.get('message','')[:60]}"]

    # 3. bite test: give each constant clue a value at a cell that is still free
    #    and assert the constraint set actually grows.
    dead = []
    for var in spec.variables:
        if var.var_type.value != "constant" or var.name in expected_dead:
            continue
        existing = sm.clues.get(var.name, {})
        spot = next((f"{r},{c}" for r in range(sm.rows) for c in range(sm.cols)
                     if f"{r},{c}" not in existing), None)
        if spot is None:
            continue
        probe = Instance(puzzle=key, rows=sm.rows, cols=sm.cols,
                         clues={k: dict(v) for k, v in sm.clues.items()},
                         regions=dict(sm.regions), params=dict(sm.params))
        # every other constant gets a value at the same spot, so companion
        # clues (e.g. an arrow paired with its number) stay consistent
        for other in spec.variables:
            if other.var_type.value == "constant":
                got = dict(probe.clues.get(other.name, {}))
                got.setdefault(spot, 1)
                probe.clues[other.name] = got
        n1, err1 = _count(spec, probe)
        if n1 is None:
            dead.append(f"{var.name}(compile error: {err1[:50]})")
        elif n1 == n0:
            dead.append(var.name)
    if dead:
        out.append(f"FAIL {key:16} clue has no effect / errors: {', '.join(dead)}")
        return out
    tag = "partial" if expected_dead else "full"
    note = f"  (unencoded: {','.join(sorted(expected_dead))})" if expected_dead else ""
    out.append(f"ok   {key:16} {n0} constraints, sample sat  [{tag}]{note}")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="verify puzzle implementations")
    parser.add_argument("keys", nargs="+")
    parser.add_argument("--backend", default="auto")
    args = parser.parse_args()
    bad = 0
    for k in args.keys:
        for line in check(k, args.backend):
            print(line)
            if line.startswith(("FAIL", "WARN")):
                bad += 1
    print(f"\n{len(args.keys) - bad}/{len(args.keys)} clean")
