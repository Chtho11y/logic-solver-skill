"""P1 loop encodings and P2 island/wall builtins."""

from __future__ import annotations

import unittest

from puzzle.backends import backend_info
from puzzle.dsl.compiler import compile_source
from puzzle.dsl.solver import STATUS_SAT, STATUS_UNSAT, solve
from puzzle.grid import Grid
from puzzle.models import PointKind, Variable


def _program(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def _shade(rows: int, cols: int) -> tuple:
    return Grid(rows, cols), [Variable("x", domain=(0, 1))]


def _edges(rows: int, cols: int) -> tuple:
    return Grid(rows, cols), [Variable("e", kind=PointKind.EDGE, domain=(0, 1))]


def _uses_graph_vertex_op(constraints) -> bool:
    from cspuz.expr import BoolExpr, Op

    stack = list(constraints)
    while stack:
        expr = stack.pop()
        if not isinstance(expr, BoolExpr):
            continue
        if expr.op == Op.GRAPH_ACTIVE_VERTICES_CONNECTED:
            return True
        stack.extend(getattr(expr, "operands", []) or [])
    return False


def _solve_on(backend: str, grid, variables, source: str):
    return solve(grid, variables, [], source, backend=backend)


class LoopEncodingTests(unittest.TestCase):
    def setUp(self) -> None:
        if not backend_info("z3").available:
            self.skipTest("cspuz Z3 backend is not installed")

    def test_one_by_one_loop_is_the_boundary_cycle(self) -> None:
        grid, variables = _edges(1, 1)
        result = _solve_on("z3", grid, variables, "loop(e)\n")
        self.assertEqual(result.status, STATUS_SAT, result.message)
        self.assertTrue(result.values["e"])
        self.assertTrue(all(value == 1 for value in result.values["e"].values()))

    def test_empty_loop_is_unsat(self) -> None:
        grid, variables = _edges(1, 1)
        source = _program(
            "for p in edges():",
            "    e[p] == 0",
            "loop(e)",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_UNSAT, result.message)

    def test_cloop_two_by_two_inner_cycle_is_sat(self) -> None:
        grid, variables = _edges(2, 2)
        result = _solve_on("z3", grid, variables, "cloop(e)\n")
        self.assertEqual(result.status, STATUS_SAT, result.message)

    def test_cloop_one_by_one_is_unsat(self) -> None:
        grid, variables = _edges(1, 1)
        result = _solve_on("z3", grid, variables, "cloop(e)\n")
        self.assertEqual(result.status, STATUS_UNSAT, result.message)

    def test_empty_connect_edges_is_unsat(self) -> None:
        grid, variables = _edges(2, 2)
        source = _program(
            "for p in edges():",
            "    e[p] == 0",
            "connect_edges(e)",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_UNSAT, result.message)

    def test_z3_loop_uses_expanded_encoding(self) -> None:
        grid, variables = _edges(2, 2)
        compiled = compile_source("use z3\nloop(e)\n", grid, variables, [])
        self.assertEqual(compiled.backend, "z3")
        self.assertFalse(_uses_graph_vertex_op(compiled.constraints))

    def test_cspuz_core_loop_uses_graph_primitive_when_installed(self) -> None:
        if not backend_info("cspuz_core").available:
            self.skipTest("cspuz_core is not installed")
        grid, variables = _edges(2, 2)
        source = "use cspuz_core\nloop(e)\n"
        compiled = compile_source(source, grid, variables, [])
        self.assertEqual(compiled.backend, "cspuz_core")
        self.assertTrue(_uses_graph_vertex_op(compiled.constraints))
        result = _solve_on("auto", grid, variables, source)
        self.assertEqual(result.status, STATUS_SAT, result.message)
        self.assertEqual(result.backend, "cspuz_core")


class IslandWallTests(unittest.TestCase):
    def setUp(self) -> None:
        if not backend_info("z3").available:
            self.skipTest("cspuz Z3 backend is not installed")

    def test_all_white_island_is_sat(self) -> None:
        grid, variables = _shade(2, 2)
        source = _program(
            "island_rule(x)",
            "for p in cells():",
            "    x[p] == 0",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_SAT, result.message)

    def test_one_black_island_is_sat(self) -> None:
        grid, variables = _shade(2, 2)
        source = _program(
            "island_rule(x)",
            "x[cell(0, 0)] == 1",
            "x[cell(0, 1)] == 0",
            "x[cell(1, 0)] == 0",
            "x[cell(1, 1)] == 0",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_SAT, result.message)

    def test_orthogonal_blacks_are_unsat(self) -> None:
        grid, variables = _shade(2, 2)
        source = _program(
            "island_rule(x)",
            "x[cell(0, 0)] == 1",
            "x[cell(0, 1)] == 1",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_UNSAT, result.message)

    def test_diagonal_blacks_split_white_and_are_unsat(self) -> None:
        grid, variables = _shade(2, 2)
        source = _program(
            "island_rule(x)",
            "x[cell(0, 0)] == 1",
            "x[cell(0, 1)] == 0",
            "x[cell(1, 0)] == 0",
            "x[cell(1, 1)] == 1",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_UNSAT, result.message)

    def test_isolated_blacks_that_split_whites_are_unsat(self) -> None:
        grid, variables = _shade(3, 3)
        source = _program(
            "island_rule(x)",
            "x[cell(0, 1)] == 1",
            "x[cell(1, 0)] == 1",
            "x[cell(1, 2)] == 1",
            "x[cell(2, 1)] == 1",
            "x[cell(0, 0)] == 0",
            "x[cell(0, 2)] == 0",
            "x[cell(1, 1)] == 0",
            "x[cell(2, 0)] == 0",
            "x[cell(2, 2)] == 0",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_UNSAT, result.message)

    def test_corner_blacks_on_three_by_three_are_sat(self) -> None:
        grid, variables = _shade(3, 3)
        source = _program(
            "island_rule(x)",
            "x[cell(0, 0)] == 1",
            "x[cell(0, 2)] == 1",
            "x[cell(2, 0)] == 1",
            "x[cell(2, 2)] == 1",
            "x[cell(0, 1)] == 0",
            "x[cell(1, 0)] == 0",
            "x[cell(1, 1)] == 0",
            "x[cell(1, 2)] == 0",
            "x[cell(2, 1)] == 0",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_SAT, result.message)

    def test_wall_all_black_two_by_two_is_unsat(self) -> None:
        grid, variables = _shade(2, 2)
        source = _program(
            "wall_rule(x)",
            "for p in cells():",
            "    x[p] == 1",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_UNSAT, result.message)

    def test_wall_l_tromino_is_sat(self) -> None:
        grid, variables = _shade(2, 2)
        source = _program(
            "wall_rule(x)",
            "x[cell(0, 0)] == 1",
            "x[cell(0, 1)] == 1",
            "x[cell(1, 0)] == 1",
            "x[cell(1, 1)] == 0",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_SAT, result.message)

    def test_wall_disconnected_blacks_are_unsat(self) -> None:
        grid, variables = _shade(2, 2)
        source = _program(
            "wall_rule(x)",
            "x[cell(0, 0)] == 1",
            "x[cell(0, 1)] == 0",
            "x[cell(1, 0)] == 0",
            "x[cell(1, 1)] == 1",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_UNSAT, result.message)

    def test_z3_island_uses_expanded_encoding(self) -> None:
        grid, variables = _shade(2, 2)
        compiled = compile_source("use z3\nisland_rule(x)\n", grid, variables, [])
        self.assertEqual(compiled.backend, "z3")
        self.assertFalse(_uses_graph_vertex_op(compiled.constraints))

    def test_cspuz_core_island_uses_graph_primitive_when_installed(self) -> None:
        if not backend_info("cspuz_core").available:
            self.skipTest("cspuz_core is not installed")
        grid, variables = _shade(2, 2)
        source = "use cspuz_core\nisland_rule(x)\n"
        compiled = compile_source(source, grid, variables, [])
        self.assertEqual(compiled.backend, "cspuz_core")
        self.assertTrue(_uses_graph_vertex_op(compiled.constraints))
        result = _solve_on("auto", grid, variables, source)
        self.assertEqual(result.status, STATUS_SAT, result.message)
        self.assertEqual(result.backend, "cspuz_core")


if __name__ == "__main__":
    unittest.main()
