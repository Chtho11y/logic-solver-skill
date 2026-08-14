"""P2 closures (``fn``) and P3 line/neighbour builtins."""

from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import z3

from puzzle.dsl.compiler import compile_source
from puzzle.dsl.errors import CompileError
from puzzle.dsl.parser import parse
from puzzle.grid import Grid
from puzzle.models import PointKind, Variable, VarType
from puzzle.spec import make_loader


def _cell(name="x", domain=(0, 1)):
    return Variable(name, PointKind.CELL, VarType.NORMAL, domain)


def _compile(source: str, variables=None, rows=3, cols=3):
    return compile_source(
        source,
        Grid(rows, cols),
        variables or [_cell()],
        [],
        z3,
        loader=make_loader(),
    )


class FnParseTests(unittest.TestCase):
    def test_parses_lambda(self) -> None:
        program = parse("let f = fn (p) -> at(x, p) == 1\n")
        self.assertEqual(len(program.statements), 1)


class ClosureTests(unittest.TestCase):
    def test_count_where_matches_loop(self) -> None:
        looped = _compile(
            """
import "core"
let n = 0
for p in cells():
    let n = n + b2i(is_black(x, p))
n == 2
"""
        )
        where = _compile(
            """
import "core"
count_where(cells(), fn (p) -> is_black(x, p)) == 2
"""
        )
        self.assertEqual(len(looped.constraints), len(where.constraints))

    def test_captures_loop_iteration_not_final(self) -> None:
        source = """
let seen = []
for i in [1, 2, 3]:
    let seen = seen.append(fn () -> i)
at(x, cell(0, 0)) == seen[0]()
at(x, cell(0, 1)) == seen[1]()
at(x, cell(0, 2)) == seen[2]()
"""
        compiled = _compile(source, [_cell("x", (0, 9))], rows=1, cols=3)
        solver = z3.Solver()
        for constraint in compiled.constraints:
            solver.add(constraint)
        self.assertEqual(solver.check(), z3.sat)
        model = solver.model()
        values = compiled.var_z3["x"]
        self.assertEqual(int(model.eval(values[(0, 0)]).as_long()), 1)
        self.assertEqual(int(model.eval(values[(0, 1)]).as_long()), 2)
        self.assertEqual(int(model.eval(values[(0, 2)]).as_long()), 3)

    def test_let_rebind_after_capture_is_invisible(self) -> None:
        source = """
let k = 1
let f = fn () -> k
let k = 2
at(x, cell(0, 0)) == f()
"""
        compiled = _compile(source, [_cell("x", (0, 9))], rows=1, cols=1)
        solver = z3.Solver()
        for constraint in compiled.constraints:
            solver.add(constraint)
        self.assertEqual(solver.check(), z3.sat)
        model = solver.model()
        self.assertEqual(int(model.eval(compiled.var_z3["x"][(0, 0)]).as_long()), 1)

    def test_def_does_not_capture(self) -> None:
        source = """
let k = 1
def f():
    return k
let k = 2
at(x, cell(0, 0)) == f()
"""
        with self.assertRaises(CompileError) as ctx:
            _compile(source, [_cell("x", (0, 9))], rows=1, cols=1)
        self.assertIn("unknown name", str(ctx.exception))

    def test_any_where_and_all_where(self) -> None:
        _compile(
            """
import "core"
any_where(cells(), fn (p) -> is_black(x, p))
all_where(row(0), fn (p) -> is_white(x, p) or is_black(x, p))
"""
        )


class NeighbourTests(unittest.TestCase):
    def test_in_grid_and_nb_default(self) -> None:
        source = """
import "core"
in_grid(cell(0, 0))
not in_grid(cell(0, 0), -1, 0)
nb(x, cell(0, 0), UP) == 0
nb_at(x, cell(0, 0), 0, 1) == at(x, cell(0, 1))
at_or(x, shift(cell(0, 0), -1, 0), 7) == 7
"""
        _compile(source, rows=2, cols=2)

    def test_dirs_and_opp(self) -> None:
        source = """
import "core"
let p = cell(1, 1)
nb(x, p, opp(DOWN)) == nb(x, p, UP)
at(x, shift(p, dr_of(RIGHT), dc_of(RIGHT))) == nb(x, p, RIGHT)
rot90(UP) == RIGHT
is_horizontal(LEFT)
not is_vertical(LEFT)
tr(1, 0, 2)[0] == 0 - 1
"""
        _compile(source, rows=3, cols=3)


class LineTests(unittest.TestCase):
    def test_rev_preserves_index_order(self) -> None:
        source = """
let r = rev(row(0))
at(x, r[0]) == at(x, cell(0, 2))
at(x, line(1, 0)[0]) == at(x, cell(0, 0))
"""
        _compile(source, rows=3, cols=3)

    def test_rev_and_merge_resorts(self) -> None:
        # Documented trap: `and` merge re-sorts via RegionValue.of.
        source = """
let r = rev(row(0)) and cell(0, 0)
at(x, r[0]) == at(x, cell(0, 0))
"""
        _compile(source, rows=1, cols=3)


class SideOfTests(unittest.TestCase):
    def test_side_of_matches_line_axis(self) -> None:
        from puzzle.dsl.builtins import _fn_side_of

        class _Pos:
            line = 1
            col = 1

        pos = _Pos()
        self.assertEqual(_fn_side_of(None, [0, 0], pos), "left")
        self.assertEqual(_fn_side_of(None, [0, 1], pos), "right")
        self.assertEqual(_fn_side_of(None, [1, 0], pos), "top")
        self.assertEqual(_fn_side_of(None, [1, 1], pos), "bottom")


class ConnectedTests(unittest.TestCase):
    def _sat(self, source: str, rows=1, cols=3) -> str:
        compiled = _compile(source, rows=rows, cols=cols)
        solver = z3.Solver()
        for constraint in compiled.constraints:
            solver.add(constraint)
        return str(solver.check())

    def test_empty_set_is_connected(self) -> None:
        status = self._sat(
            """
import "core"
for p in cells():
    at(x, p) == 0
connected(x, 1)
"""
        )
        self.assertEqual(status, "sat")

    def test_one_blob_is_connected(self) -> None:
        status = self._sat(
            """
import "core"
at(x, cell(0, 0)) == 1
at(x, cell(0, 1)) == 1
at(x, cell(0, 2)) == 0
connected(x, 1)
"""
        )
        self.assertEqual(status, "sat")

    def test_two_blobs_not_connected(self) -> None:
        status = self._sat(
            """
import "core"
at(x, cell(0, 0)) == 1
at(x, cell(0, 1)) == 0
at(x, cell(0, 2)) == 1
connected(x, 1)
"""
        )
        self.assertEqual(status, "unsat")

    def test_diagonal_needs_connected8(self) -> None:
        source4 = """
import "core"
at(x, cell(0, 0)) == 1
at(x, cell(0, 1)) == 0
at(x, cell(1, 0)) == 0
at(x, cell(1, 1)) == 1
is_connected(x, 1)
"""
        source8 = source4.replace("is_connected", "is_connected8")
        self.assertEqual(self._sat(source4, rows=2, cols=2), "unsat")
        self.assertEqual(self._sat(source8, rows=2, cols=2), "sat")

    def test_official_names_compile(self) -> None:
        from puzzle.dsl.builtins import BUILTIN_FUNCTIONS

        self.assertEqual(BUILTIN_FUNCTIONS["cc_id"].alias_of, "component_id")
        self.assertEqual(BUILTIN_FUNCTIONS["cc_size"].alias_of, "component_size")
        self.assertEqual(BUILTIN_FUNCTIONS["cc_count"].alias_of, "component_count")
        _compile("same_component(x, cell(0, 0), cell(0, 1))\n", rows=2, cols=2)
        _compile("at(component_id(x), cell(0, 0)) >= 0\n", rows=2, cols=2)
        _compile("at(component_size(x), cell(0, 0)) >= 1\n", rows=2, cols=2)

    def test_is_connected_memo_is_not_valuecc(self) -> None:
        compiled = _compile(
            """
import "core"
is_connected(x, 1)
""",
            rows=2,
            cols=2,
        )
        blob = "\n".join(c.sexpr() for c in compiled.constraints)
        self.assertIn("isconn", blob)
        self.assertNotIn("#cc4#id", blob)

    def test_l2_names_still_build_ids(self) -> None:
        compiled = _compile("component_count(x, 1) <= 1\n", rows=2, cols=2)
        blob = "\n".join(c.sexpr() for c in compiled.constraints)
        self.assertIn("#cc4#id", blob)


if __name__ == "__main__":
    unittest.main()
