"""Meta-solve (``meta:`` / ``scope:`` / uniqueness) tests — META_SOLVE_PLAN PM-1..3."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import z3

from puzzle.dsl.compiler import compile_source
from puzzle.dsl.errors import CompileError
from puzzle.dsl.session import Z3Session
from puzzle.dsl.solver import compile_only
from puzzle.grid import Grid
from puzzle.models import PointKind, Variable, VarType
from puzzle.runner import solve_instance
from puzzle.spec import load_sample, load_spec, make_loader
from tools.baseline import _compile, instance_for
from tools.uniqueness import check_uniqueness


BASELINE_P1S2 = Path(ROOT) / "docs" / "baseline" / "9de3db1b33b8-p1s2.json"


def _cell_var(name="x", domain=(0, 1)):
    return Variable(name, PointKind.CELL, VarType.NORMAL, domain)


def _edge_var(name="e"):
    return Variable(name, PointKind.EDGE, VarType.NORMAL, (0, 1))


def _cc_var(name="c"):
    return Variable(name, PointKind.CELL, VarType.CC, None)


def _compile_src(source: str, variables, rows=3, cols=3, run_meta=True, regions=()):
    grid = Grid(rows, cols)
    session = Z3Session(z3, timeout_ms=5000, seed=1) if run_meta else None
    return compile_source(
        source,
        grid,
        variables,
        list(regions),
        z3,
        loader=make_loader(),
        session=session,
        run_meta=run_meta,
        timeout_ms=5000,
    )


class Pm0BaselineTests(unittest.TestCase):
    def test_run_meta_false_constraint_counts_match_p1s2(self) -> None:
        data = json.loads(BASELINE_P1S2.read_text(encoding="utf-8"))
        want = {row["key"]: row["constraints"] for row in data["keys"]}
        # sudoku / yajilin do not use L1 connectivity. nurikabe / context call
        # connected() (now is_connected); their counts are allowed to move.
        for key in ("sudoku", "yajilin"):
            spec = load_spec(key)
            instance, _case, _kind = instance_for(key)
            self.assertIsNotNone(instance)
            status, count, message = _compile(spec, instance)
            self.assertEqual(status, "ok", f"{key}: {message}")
            self.assertEqual(count, want[key], f"{key} constraint count drifted")
        for key in ("nurikabe", "context"):
            spec = load_spec(key)
            instance, _case, _kind = instance_for(key)
            self.assertIsNotNone(instance)
            status, _count, message = _compile(spec, instance)
            self.assertEqual(status, "ok", f"{key}: {message}")


class MetaSkipTests(unittest.TestCase):
    def test_run_meta_false_skips_block(self) -> None:
        source = """
x[cell(0, 0)] == 0
meta:
    fail("should not run")
"""
        compiled = _compile_src(source, [_cell_var()], run_meta=False)
        self.assertTrue(any("skipped meta" in line for line in compiled.debug))

    def test_compile_only_skips_meta(self) -> None:
        source = """
x[cell(0, 0)] == 0
meta:
    fail("compile_only must not run meta")
"""
        result = compile_only(
            Grid(2, 2),
            [_cell_var()],
            [],
            source,
            loader=make_loader(),
        )
        self.assertEqual(result.status, "compiled", result.message)

    def test_solve_outside_meta_is_error(self) -> None:
        with self.assertRaises(CompileError) as ctx:
            _compile_src("let s = solve()\n", [_cell_var()], run_meta=True)
        self.assertIn("meta:", str(ctx.exception))

    def test_scope_outside_meta_is_error(self) -> None:
        with self.assertRaises(CompileError) as ctx:
            _compile_src("scope:\n    x[cell(0, 0)] == 0\n", [_cell_var()], run_meta=True)
        self.assertIn("meta:", str(ctx.exception))

    def test_def_inside_meta_is_error(self) -> None:
        with self.assertRaises(CompileError) as ctx:
            _compile_src("meta:\n    def f():\n        fail(\"no\")\n", [_cell_var()], run_meta=True)
        self.assertIn("def", str(ctx.exception))


class MetaSolveTests(unittest.TestCase):
    def test_solve_snapshot_matches_pinned_cells(self) -> None:
        source = """
x[cell(0, 0)] == 1
x[cell(0, 1)] == 0
meta:
    let s = solve()
    require(s.sat, "expected sat")
    require(at(s.x, cell(0, 0)) == 1, "cell 0,0")
    require(at(s.x, cell(0, 1)) == 0, "cell 0,1")
"""
        _compile_src(source, [_cell_var()], rows=2, cols=2, run_meta=True)

    def test_solve_snapshot_matches_solve_instance(self) -> None:
        spec = load_spec("sudoku")
        inst = load_sample("sudoku")
        self.assertIsNotNone(inst)
        free = solve_instance(spec, inst, timeout_ms=30000)
        self.assertEqual(free["status"], "sat", free.get("message", "")[:200])
        want = int((free.get("values") or {}).get("x", {}).get("0,0"))
        source = spec.source + f"""
meta:
    let s = solve()
    require(s.sat, "expected sat")
    require(at(s.x, cell(0, 0)) == {want}, "cell 0,0 mismatch")
"""
        result = solve_instance(spec, inst, timeout_ms=30000, source=source, run_meta=True)
        self.assertEqual(result["status"], "sat", result.get("message", "")[:200])


class ScopeRollbackTests(unittest.TestCase):
    def test_scope_constraint_does_not_leak(self) -> None:
        source = """
meta:
    let s0 = solve()
    require(s0.sat, "empty should be sat")
    scope:
        x[cell(0, 0)] == 1
        x[cell(0, 0)] == 0
        let s1 = solve()
        require(not s1.sat, "contradiction inside scope")
    let s2 = solve()
    require(s2.sat, "contradiction leaked out of scope")
"""
        _compile_src(source, [_cell_var()], rows=2, cols=2, run_meta=True)

    def test_scope_cloop_memo_rollback(self) -> None:
        source = """
meta:
    scope:
        cloop(e)
    cloop(e)
    let s = solve()
    require(s.sat, "cloop after scope should still encode")
"""
        before = _compile_src("cloop(e)\n", [_edge_var()], rows=3, cols=3, run_meta=False)
        after = _compile_src(source, [_edge_var()], rows=3, cols=3, run_meta=True)
        self.assertEqual(len(before.constraints), len(after.constraints))

    def test_scope_cc_size_rollback(self) -> None:
        source = """
meta:
    scope:
        c.size[cell(0, 0)] == 1
    c.size[cell(0, 0)] == 9
    let s = solve()
    require(s.sat, "cc.size after scope")
    require(at(s.c, cell(0, 0)) == at(s.c, cell(2, 2)), "one region")
"""
        before = _compile_src(
            "c.size[cell(0, 0)] == 9\n",
            [_cc_var()],
            rows=3,
            cols=3,
            run_meta=False,
        )
        after = _compile_src(source, [_cc_var()], rows=3, cols=3, run_meta=True)
        self.assertEqual(len(before.constraints), len(after.constraints))


class UniqueTests(unittest.TestCase):
    def test_pinned_cell_is_unique(self) -> None:
        source = """
import "meta"
x[cell(0, 0)] == 1
assert_unique(x)
"""
        _compile_src(source, [_cell_var()], rows=1, cols=1, run_meta=True)

    def test_free_cell_is_multiple(self) -> None:
        source = """
import "meta"
assert_unique(x)
"""
        with self.assertRaises(CompileError) as ctx:
            _compile_src(source, [_cell_var()], rows=1, cols=1, run_meta=True)
        self.assertIn("MULTIPLE", str(ctx.exception))

    def test_sudoku_sample_is_unique(self) -> None:
        spec = load_spec("sudoku")
        inst = load_sample("sudoku")
        self.assertIsNotNone(inst)
        result = check_uniqueness(spec, inst, timeout_ms=30000)
        self.assertEqual(result["status"], "unique", result.get("message", "")[:200])

    def test_yajilin_empty_is_multiple(self) -> None:
        spec = load_spec("yajilin")
        inst = load_sample("yajilin")
        self.assertIsNotNone(inst)
        result = check_uniqueness(spec, inst, timeout_ms=30000)
        self.assertEqual(result["status"], "multiple", result.get("message", "")[:200])

    def test_b_class_samples_are_multiple(self) -> None:
        for key in ("statuepark", "pentopia", "parquet", "wagiri", "hinge"):
            with self.subTest(key=key):
                spec = load_spec(key)
                inst = load_sample(key)
                self.assertIsNotNone(inst, key)
                result = check_uniqueness(spec, inst, timeout_ms=30000)
                self.assertEqual(
                    result["status"],
                    "multiple",
                    f"{key}: {result.get('message', '')[:200]}",
                )


if __name__ == "__main__":
    unittest.main()
