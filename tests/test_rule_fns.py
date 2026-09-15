"""Imported impls expose a rule function; top-level constraints are not applied."""

from __future__ import annotations

import unittest

from puzzle.dsl.solver import STATUS_COMPILED, STATUS_SAT, STATUS_UNSAT, compile_only, solve
from puzzle.grid import Grid
from puzzle.models import Variable
from puzzle.spec import make_loader


def _sudoku_grid(n: int, givens: dict | None = None) -> tuple[Grid, list[Variable]]:
    return Grid(n, n), [Variable("x", domain=(1, 9), givens=dict(givens or {}))]


class RuleFnTests(unittest.TestCase):
    def test_import_sudoku_does_not_apply_latin(self) -> None:
        ones = {(r, c): 1 for r in range(2) for c in range(2)}
        grid, variables = _sudoku_grid(2, ones)
        result = solve(
            grid,
            variables,
            [],
            'import "sudoku"\ntrue\n',
            backend="z3",
            loader=make_loader(),
        )
        self.assertEqual(result.status, STATUS_SAT, result.message)

    def test_calling_sudoku_applies_latin(self) -> None:
        ones = {(r, c): 1 for r in range(2) for c in range(2)}
        grid, variables = _sudoku_grid(2, ones)
        result = solve(
            grid,
            variables,
            [],
            'import "sudoku"\nsudoku(x)\n',
            backend="z3",
            loader=make_loader(),
        )
        self.assertEqual(result.status, STATUS_UNSAT, result.message)

    def test_sudoku_call_compiles_on_9x9(self) -> None:
        grid, variables = _sudoku_grid(9)
        result = compile_only(
            grid,
            variables,
            [],
            'import "sudoku"\nsudoku(x)\n',
            loader=make_loader(),
        )
        self.assertEqual(result.status, STATUS_COMPILED, result.message)
        self.assertGreater(result.constraint_count, 0)

    def test_bundled_sudoku_source_still_calls_itself(self) -> None:
        from puzzle.spec import load_spec

        spec = load_spec("sudoku")
        self.assertIn("def sudoku(x):", spec.source)
        self.assertIn("sudoku(x)", spec.source.split("def sudoku(x):", 1)[1])
        grid, variables = _sudoku_grid(9)
        result = compile_only(
            grid,
            variables,
            [],
            spec.source,
            loader=make_loader(),
        )
        self.assertEqual(result.status, STATUS_COMPILED, result.message)


if __name__ == "__main__":
    unittest.main()
