"""DSL ``use`` backend selection and P0 connected encodings."""

from __future__ import annotations

import unittest

from puzzle.backends import (
    BackendError,
    backend_info,
    features_for,
    merge_backend_request,
)
from puzzle.dsl.compiler import compile_source, declared_backend
from puzzle.dsl.parser import parse
from puzzle.dsl.solver import (
    STATUS_COMPILED,
    STATUS_ERROR,
    STATUS_SAT,
    STATUS_UNSAT,
    compile_only,
    solve,
)
from puzzle.grid import Grid
from puzzle.models import Variable


def _shade(rows: int = 2, cols: int = 2) -> tuple:
    return Grid(rows, cols), [Variable("x", domain=(0, 1))]


def _program(*lines: str) -> str:
    return "\n".join(lines) + "\n"


class UseKeywordTests(unittest.TestCase):
    def test_parse_name_and_string(self) -> None:
        program = parse('use cspuz_core\ntrue\n')
        self.assertEqual(declared_backend(program), "cspuz_core")
        program = parse('use "z3"\ntrue\n')
        self.assertEqual(declared_backend(program), "z3")
        program = parse("true\n")
        self.assertIsNone(declared_backend(program))

    def test_unknown_backend_is_compile_error(self) -> None:
        result = compile_only(Grid(1, 1), [], [], "use banana\ntrue\n")
        self.assertEqual(result.status, STATUS_ERROR)
        self.assertIn("unknown solver backend", result.message)

    def test_nested_use_is_rejected(self) -> None:
        source = _program("if true:", "    use z3")
        result = compile_only(Grid(1, 1), [], [], source)
        self.assertEqual(result.status, STATUS_ERROR)
        self.assertIn("top-level", result.message)

    def test_conflicting_use_is_rejected(self) -> None:
        result = compile_only(Grid(1, 1), [], [], "use z3\nuse cspuz_core\ntrue\n")
        self.assertEqual(result.status, STATUS_ERROR)
        self.assertIn("conflicting", result.message)

    def test_use_in_imported_module_is_rejected(self) -> None:
        grid, variables = _shade(1, 1)
        result = solve(
            grid,
            variables,
            [],
            'import "evil"\nat(x, cell(0, 0)) == 0\n',
            backend="z3",
            loader=lambda name: "use z3\n" if name == "evil" else (_ for _ in ()).throw(
                FileNotFoundError(name)
            ),
        )
        self.assertEqual(result.status, STATUS_ERROR)
        self.assertIn("main program", result.message)

    def test_api_and_dsl_conflict(self) -> None:
        grid, variables = _shade(1, 1)
        result = solve(
            grid,
            variables,
            [],
            "use z3\nat(x, cell(0, 0)) == 0\n",
            backend="cspuz_core",
        )
        self.assertEqual(result.status, STATUS_ERROR)
        self.assertIn("backend conflict", result.message)

    def test_merge_prefers_explicit_use_over_auto(self) -> None:
        self.assertEqual(
            merge_backend_request(api="auto", dsl="cspuz_core"), "cspuz_core"
        )
        self.assertEqual(merge_backend_request(api="z3", dsl=None), "z3")
        with self.assertRaises(BackendError):
            merge_backend_request(api="z3", dsl="cspuz_core")


class ConnectedEncodingTests(unittest.TestCase):
    def setUp(self) -> None:
        if not backend_info("z3").available:
            self.skipTest("cspuz Z3 backend is not installed")

    def test_catalogue_advertises_features(self) -> None:
        z3 = backend_info("z3").to_json()
        self.assertIn("timeout", z3["features"])
        self.assertNotIn("graph_vertex_connected", z3["features"])
        self.assertFalse(features_for("z3").graph_vertex_connected)
        self.assertTrue(features_for("cspuz_core").graph_vertex_connected)

    def test_empty_and_full_black_are_connected(self) -> None:
        grid, variables = _shade()
        empty = solve(
            grid,
            variables,
            [],
            _program(
                "for p in cells():",
                "    x[p] == 0",
                "connected(x, 1)",
            ),
            backend="z3",
        )
        self.assertEqual(empty.status, STATUS_SAT, empty.message)
        filled = solve(
            grid,
            variables,
            [],
            _program(
                "for p in cells():",
                "    x[p] == 1",
                "connected(x, 1)",
            ),
            backend="z3",
        )
        self.assertEqual(filled.status, STATUS_SAT, filled.message)

    def test_diagonal_is_unsat_for_connected_and_sat_for_connected8(self) -> None:
        grid, variables = _shade()
        diagonal = _program(
            "x[cell(0, 0)] == 1",
            "x[cell(0, 1)] == 0",
            "x[cell(1, 0)] == 0",
            "x[cell(1, 1)] == 1",
        )
        four = solve(
            grid, variables, [], diagonal + "connected(x, 1)\n", backend="z3"
        )
        eight = solve(
            grid, variables, [], diagonal + "connected8(x, 1)\n", backend="z3"
        )
        self.assertEqual(four.status, STATUS_UNSAT, four.message)
        self.assertEqual(eight.status, STATUS_SAT, eight.message)

    def test_use_z3_selects_expanded_encoding(self) -> None:
        grid, variables = _shade()
        compiled = compile_source(
            _program("use z3", "connected(x, 1)"),
            grid,
            variables,
            [],
        )
        self.assertEqual(compiled.backend, "z3")
        self.assertNotIn("graph_vertex_connected", compiled.features)
        self.assertFalse(_uses_graph_vertex_op(compiled.constraints))

    def test_cspuz_core_uses_graph_primitive_when_installed(self) -> None:
        if not backend_info("cspuz_core").available:
            self.skipTest("cspuz_core is not installed")
        grid, variables = _shade()
        source = _program("use cspuz_core", "connected(x, 1)")
        compiled = compile_source(source, grid, variables, [])
        self.assertEqual(compiled.backend, "cspuz_core")
        self.assertIn("graph_vertex_connected", compiled.features)
        self.assertTrue(_uses_graph_vertex_op(compiled.constraints))
        result = solve(grid, variables, [], source, backend="auto")
        self.assertEqual(result.status, STATUS_SAT, result.message)
        self.assertEqual(result.backend, "cspuz_core")

    def test_compile_only_records_backend(self) -> None:
        grid, variables = _shade(1, 1)
        result = compile_only(
            grid, variables, [], "use z3\nat(x, cell(0, 0)) == 0\n"
        )
        self.assertEqual(result.status, STATUS_COMPILED, result.message)
        self.assertEqual(result.backend, "z3")


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


if __name__ == "__main__":
    unittest.main()
