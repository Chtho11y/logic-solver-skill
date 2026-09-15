"""P3 graph_division encodings for cc_size / groups_of_size / CC .size."""

from __future__ import annotations

import unittest

from puzzle.backends import backend_info
from puzzle.dsl.compiler import compile_source
from puzzle.dsl.solver import STATUS_SAT, STATUS_UNSAT, solve
from puzzle.grid import Grid
from puzzle.models import Variable, VarType
from puzzle.runner import solve_instance
from puzzle.spec import load_sample, load_spec


def _program(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def _shade(rows: int, cols: int) -> tuple:
    return Grid(rows, cols), [Variable("x", domain=(0, 1))]


def _cc(rows: int, cols: int) -> tuple:
    return Grid(rows, cols), [Variable("c", var_type=VarType.CC)]


def _uses_graph_division(constraints) -> bool:
    from cspuz.expr import BoolExpr, Op

    stack = list(constraints)
    while stack:
        expr = stack.pop()
        if not isinstance(expr, BoolExpr):
            continue
        if expr.op == Op.GRAPH_DIVISION:
            return True
        stack.extend(getattr(expr, "operands", []) or [])
    return False


def _solve_on(backend: str, grid, variables, source: str):
    return solve(grid, variables, [], source, backend=backend)


class CcSizeDivisionTests(unittest.TestCase):
    def setUp(self) -> None:
        if not backend_info("z3").available:
            self.skipTest("cspuz Z3 backend is not installed")

    def test_groups_of_size_full_black_two_by_two_is_sat(self) -> None:
        grid, variables = _shade(2, 2)
        source = _program(
            "let sz = cc_size(x)",
            "for p in cells():",
            "    at(x, p) == 1",
            "    at(sz, p) == 4",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_SAT, result.message)
        self.assertTrue(all(value == 1 for value in result.values["x"].values()))

    def test_groups_of_size_three_cell_island_is_unsat(self) -> None:
        grid, variables = _shade(2, 2)
        source = _program(
            "let sz = cc_size(x)",
            "for p in cells():",
            "    at(x, p) == 1 => at(sz, p) == 2",
            "at(x, cell(0, 0)) == 1",
            "at(x, cell(0, 1)) == 1",
            "at(x, cell(1, 0)) == 1",
            "at(x, cell(1, 1)) == 0",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_UNSAT, result.message)

    def test_cc_id_all_black_two_by_two_is_min_linear_index(self) -> None:
        grid, variables = _shade(2, 2)
        source = _program(
            "for p in cells():",
            "    at(x, p) == 1",
            "    at(cc_id(x), p) == 0",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_SAT, result.message)

    def test_cc_id_disconnected_blacks_keep_distinct_roots(self) -> None:
        grid, variables = _shade(2, 2)
        source = _program(
            "at(x, cell(0, 0)) == 1",
            "at(x, cell(0, 1)) == 0",
            "at(x, cell(1, 0)) == 0",
            "at(x, cell(1, 1)) == 1",
            "at(cc_id(x), cell(0, 0)) == 0",
            "at(cc_id(x), cell(1, 1)) == 3",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_SAT, result.message)

    def test_cc_count_two_white_islands(self) -> None:
        grid, variables = _shade(2, 2)
        source = _program(
            "at(x, cell(0, 0)) == 0",
            "at(x, cell(0, 1)) == 1",
            "at(x, cell(1, 0)) == 1",
            "at(x, cell(1, 1)) == 0",
            "cc_count(x, 0) == 2",
            "cc_count(x, 1) == 2",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_SAT, result.message)

    def test_cc_variable_size_does_not_change_min_linear_ids(self) -> None:
        grid, variables = _cc(2, 2)
        source = _program(
            "for p in cells():",
            "    at(c.size, p) == 4",
        )
        result = _solve_on("z3", grid, variables, source)
        self.assertEqual(result.status, STATUS_SAT, result.message)
        self.assertEqual(
            result.values["c"],
            {(0, 0): 0, (0, 1): 0, (1, 0): 0, (1, 1): 0},
        )

    def test_z3_cc_size_does_not_emit_graph_division_op(self) -> None:
        grid, variables = _shade(2, 2)
        compiled = compile_source("use z3\nlet sz = cc_size(x)\nat(sz, cell(0, 0)) >= 1\n", grid, variables, [])
        self.assertEqual(compiled.backend, "z3")
        self.assertFalse(_uses_graph_division(compiled.constraints))

    def test_cspuz_core_cc_size_emits_graph_division_when_installed(self) -> None:
        if not backend_info("cspuz_core").available:
            self.skipTest("cspuz_core is not installed")
        grid, variables = _shade(2, 2)
        source = "use cspuz_core\nlet sz = cc_size(x)\nat(sz, cell(0, 0)) >= 1\n"
        compiled = compile_source(source, grid, variables, [])
        self.assertEqual(compiled.backend, "cspuz_core")
        self.assertTrue(_uses_graph_division(compiled.constraints))
        result = _solve_on("auto", grid, variables, source)
        self.assertEqual(result.status, STATUS_SAT, result.message)
        self.assertEqual(result.backend, "cspuz_core")

    def test_cspuz_core_cc_variable_size_emits_graph_division(self) -> None:
        if not backend_info("cspuz_core").available:
            self.skipTest("cspuz_core is not installed")
        grid, variables = _cc(2, 2)
        source = "use cspuz_core\nat(c.size, cell(0, 0)) >= 1\n"
        compiled = compile_source(source, grid, variables, [])
        self.assertTrue(_uses_graph_division(compiled.constraints))

    def test_nurikabe_sample_sat_on_available_backends(self) -> None:
        spec = load_spec("nurikabe")
        instance = load_sample("nurikabe")
        self.assertIsNotNone(instance)
        backends = ["z3"]
        if backend_info("cspuz_core").available:
            backends.append("cspuz_core")
        statuses = []
        for backend in backends:
            timeout = 60000 if backend == "z3" else None
            result = solve_instance(spec, instance, backend=backend, timeout_ms=timeout)
            self.assertEqual(result["status"], "sat", result.get("message"))
            statuses.append(result["status"])
        self.assertEqual(len(set(statuses)), 1)

    def test_tetrochain_sample_sat_on_available_backends(self) -> None:
        spec = load_spec("tetrochain")
        instance = load_sample("tetrochain")
        self.assertIsNotNone(instance)
        backends = ["z3"]
        if backend_info("cspuz_core").available:
            backends.append("cspuz_core")
        for backend in backends:
            timeout = 120000 if backend == "z3" else None
            result = solve_instance(spec, instance, backend=backend, timeout_ms=timeout)
            self.assertEqual(result["status"], "sat", f"{backend}: {result.get('message')}")

    def test_fillomino_sample_keeps_cc_ids(self) -> None:
        spec = load_spec("fillomino")
        instance = load_sample("fillomino")
        self.assertIsNotNone(instance)
        result = solve_instance(spec, instance, backend="z3", timeout_ms=60000)
        self.assertEqual(result["status"], "sat", result.get("message"))
        ids = result["values"]["c"]
        cols = instance.cols
        groups: dict[int, list[tuple[int, int]]] = {}
        for key, value in ids.items():
            row, col = (int(part) for part in key.split(","))
            groups.setdefault(value, []).append((row, col))
        for region_id, cells in groups.items():
            self.assertEqual(region_id, min(row * cols + col for row, col in cells))
