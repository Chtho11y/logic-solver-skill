"""Regression tests for DSL control flow and composable constraints."""

from __future__ import annotations

import unittest
from textwrap import dedent

from puzzle.backends import backend_info
from puzzle.dsl.solver import STATUS_ERROR, STATUS_SAT, STATUS_UNSAT, compile_only, solve
from puzzle.grid import Grid
from puzzle.models import PointKind, Region, Variable
from puzzle.spec import make_loader


class DslSemanticTests(unittest.TestCase):
    def setUp(self) -> None:
        if not backend_info("z3").available:
            self.skipTest("cspuz Z3 backend is not installed")

    def assert_status(self, source, expected, *, grid=None, variables=None, regions=None):
        result = solve(
            grid if grid is not None else Grid(1, 1),
            variables if variables is not None else [],
            regions if regions is not None else [],
            dedent(source).strip(),
            loader=make_loader(),
            backend="z3",
            timeout_ms=5000,
        )
        self.assertEqual(result.status, expected, result.message)
        return result


class ControlFlowTests(DslSemanticTests):
    def test_symbolic_returns_are_rejected_at_the_return(self) -> None:
        bodies = (
            "    if c:\n        return 1\n    return 0",
            "    if c:\n        true\n    else:\n        return 0",
            "    if false:\n        return 2\n    elif c:\n        return 1\n    return 0",
            "    if c:\n        true\n    elif true:\n        return 1\n    return 0",
            "    if c:\n        if true:\n            return 1\n    return 0",
            "    if c:\n        for i in [1]:\n            return i\n    return 0",
            "    if c:\n        return\n    return 0",
            "    if c:\n        return unknown_name\n    return 0",
        )
        for body in bodies:
            for given in (0, 1):
                with self.subTest(body=body, given=given):
                    source = "def pick(c):\n" + body + "\npick(at(x, cell(0, 0)) == 1) == 1"
                    result = compile_only(
                        Grid(1, 1),
                        [Variable("x", domain=(0, 1), givens={(0, 0): given})],
                        [],
                        source,
                    )
                    self.assertEqual(result.status, STATUS_ERROR, result.message)
                    self.assertIn("compile-time if", result.message)
                    self.assertIn("ite", result.message)
                    self.assertIsNotNone(result.error_line)
                    self.assertTrue(source.splitlines()[result.error_line - 1].strip().startswith("return"))

    def test_compile_time_branches_and_plain_returns_are_allowed(self) -> None:
        self.assert_status(
            """
            def pick(c):
                if c:
                    return 1
                else:
                    return 0
            def choose():
                if false:
                    return 0
                elif true:
                    return 2
                return 3
            pick(true) == 1
            pick(false) == 0
            choose() == 2
            """,
            STATUS_SAT,
        )

    def test_ite_returns_a_symbolic_value(self) -> None:
        for given in (0, 1):
            for expected in (0, 1):
                with self.subTest(given=given, expected=expected):
                    self.assert_status(
                        "def pick(c):\n    return ite(c, 1, 0)\n"
                        f"pick(at(x, cell(0, 0)) == 1) == {expected}",
                        STATUS_SAT if expected == given else STATUS_UNSAT,
                        variables=[Variable("x", domain=(0, 1), givens={(0, 0): given})],
                    )

    def test_inherited_guards_allow_returns_and_still_guard_constraints(self) -> None:
        source = """
            def inner(c):
                if c:
                    at(x, cell(0, 0)) == 0
                    return 7
                return 8
            def outer():
                return inner(true)
            if at(x, cell(0, 0)) == 1:
                for p in cells():
                    outer() == 7
            outer == outer
        """
        source = source.replace("            outer == outer\n", "")
        for given in (0, 1):
            with self.subTest(given=given):
                self.assert_status(
                    source,
                    STATUS_SAT if given == 0 else STATUS_UNSAT,
                    variables=[Variable("x", domain=(0, 1), givens={(0, 0): given})],
                )

    def test_nested_call_restores_the_enclosing_return_guard(self) -> None:
        self.assert_status(
            """
            def inner():
                return 1
            def outer(c):
                if c:
                    inner() == 1
                    return 1
                return 0
            outer(at(x, cell(0, 0)) == 1) == 1
            """,
            STATUS_ERROR,
            variables=[Variable("x", domain=(0, 1))],
        )

    def test_return_after_symbolic_branch_is_allowed(self) -> None:
        self.assert_status(
            """
            def value(c):
                if c:
                    true
                return 1
            value(at(x, cell(0, 0)) == 1) == 1
            """,
            STATUS_SAT,
            variables=[Variable("x", domain=(0, 1))],
        )

    def test_return_outside_function_reports_control_flow_error_first(self) -> None:
        result = self.assert_status("return unknown_name", STATUS_ERROR)
        self.assertIn("outside of a def", result.message)
        self.assertEqual(result.error_line, 1)


class LinkPredicateTests(DslSemanticTests):
    def variables(self, outer, *, gate=0, closed=True):
        givens = {edge: 0 for edge in Grid(2, 2).edges()}
        for edge in (("H", 1, 0), ("H", 1, 1), ("V", 0, 1), ("V", 1, 1)):
            givens[edge] = int(closed)
        givens[("H", 0, 0)] = outer
        return [
            Variable("e", kind=PointKind.EDGE, domain=(0, 1), givens=givens),
            Variable("x", domain=(0, 1), givens={(0, 0): gate}),
        ]

    def test_false_symbolic_branch_does_not_restrict_outer_edges(self) -> None:
        for name in ("cloop", "connect_links"):
            for gate in (0, 1):
                with self.subTest(name=name, gate=gate):
                    self.assert_status(
                        f"if at(x, cell(0, 0)) == 1:\n    {name}(e)",
                        STATUS_SAT if gate == 0 else STATUS_UNSAT,
                        grid=Grid(2, 2),
                        variables=self.variables(1, gate=gate),
                    )

    def test_predicates_include_outer_edges_in_their_boolean_result(self) -> None:
        for name in ("cloop", "connect_links"):
            for outer in (0, 1):
                cases = (
                    (f"{name}(e)", STATUS_SAT if outer == 0 else STATUS_UNSAT),
                    (f"not {name}(e)", STATUS_UNSAT if outer == 0 else STATUS_SAT),
                    (f"true or {name}(e)", STATUS_SAT),
                    (f"false => {name}(e)", STATUS_SAT),
                    (f"let valid = {name}(e)\ntrue", STATUS_SAT),
                )
                for source, expected in cases:
                    with self.subTest(source=source, outer=outer):
                        self.assert_status(source, expected, grid=Grid(2, 2), variables=self.variables(outer))

    def test_empty_links_are_not_a_connected_nonempty_loop(self) -> None:
        for name in ("cloop", "connect_links"):
            with self.subTest(name=name):
                self.assert_status(f"{name}(e)", STATUS_UNSAT, grid=Grid(2, 2), variables=self.variables(0, closed=False))
                self.assert_status(f"not {name}(e)", STATUS_SAT, grid=Grid(2, 2), variables=self.variables(0, closed=False))

    def test_cached_connectivity_does_not_leak_constraints_between_calls(self) -> None:
        for first, second in (("cloop", "connect_links"), ("connect_links", "cloop"), ("cloop", "cloop")):
            with self.subTest(first=first, second=second):
                source = f"if at(x, cell(0, 0)) == 1:\n    {first}(e)\n"
                self.assert_status(
                    source + f"not {second}(e)", STATUS_SAT,
                    grid=Grid(2, 2), variables=self.variables(1),
                )
                self.assert_status(
                    source + f"{second}(e)", STATUS_UNSAT,
                    grid=Grid(2, 2), variables=self.variables(1),
                )
                self.assert_status(
                    source + f"{second}(e)", STATUS_SAT,
                    grid=Grid(2, 2), variables=self.variables(0),
                )


class RegionGroupTests(DslSemanticTests):
    def test_exactly_one_black_group_in_each_region(self) -> None:
        regions = [
            Region("a", PointKind.CELL, ((0, 0), (0, 1), (0, 2))),
            Region("b", PointKind.CELL, ((0, 3),)),
        ]
        for values, expected in (
            ("1010", STATUS_UNSAT),
            ("0001", STATUS_UNSAT),
            ("1000", STATUS_UNSAT),
            ("1111", STATUS_UNSAT),
            ("1001", STATUS_SAT),
            ("1101", STATUS_SAT),
        ):
            with self.subTest(values=values):
                self.assert_status(
                    'import "shading"\none_black_group_per_region(x)', expected,
                    grid=Grid(1, 4), regions=regions,
                    variables=[Variable("x", domain=(0, 1), givens={(0, c): int(v) for c, v in enumerate(values)})],
                )

    def test_at_most_one_group_still_allows_empty_regions(self) -> None:
        self.assert_status(
            'import "shading"\nat_most_one_black_group_per_region(x)', STATUS_SAT,
            grid=Grid(1, 2),
            regions=[Region("a", PointKind.CELL, ((0, 0),)), Region("b", PointKind.CELL, ((0, 1),))],
            variables=[Variable("x", domain=(0, 1), givens={(0, 0): 1, (0, 1): 0})],
        )


if __name__ == "__main__":
    unittest.main()
