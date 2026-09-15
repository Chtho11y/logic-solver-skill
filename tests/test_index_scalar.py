"""Singleton region index is a scalar; multi-point index stays a list."""

from __future__ import annotations

import unittest

from puzzle.dsl.solver import solve
from puzzle.grid import Grid
from puzzle.models import Variable


class IndexScalarTests(unittest.TestCase):
    def test_singleton_and_is_logical_not_list_merge(self) -> None:
        # If x[p] were a length-1 list, `and` would concatenate and `=>` would
        # broadcast element-wise, making this unsat. With a scalar index it is sat.
        result = solve(
            Grid(1, 2),
            [Variable("x", domain=(0, 1))],
            [],
            "\n".join(
                [
                    "(x[cell(0, 0)] == 1 and x[cell(0, 1)] == 0) => false",
                    "x[cell(0, 0)] == 1",
                    "x[cell(0, 1)] == 1",
                ]
            ),
            backend="z3",
        )
        self.assertTrue(result.ok, result.message)

    def test_row_index_still_broadcasts_as_a_list(self) -> None:
        result = solve(
            Grid(1, 2),
            [Variable("x", domain=(0, 1))],
            [],
            "sum(x[row(0)]) == 2",
            backend="z3",
        )
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.values["x"], {(0, 0): 1, (0, 1): 1})

    def test_at_alias_matches_index(self) -> None:
        result = solve(
            Grid(1, 1),
            [Variable("x", domain=(0, 1))],
            [],
            "at(x, cell(0, 0)) == x[cell(0, 0)]\nx[cell(0, 0)] == 1",
            backend="z3",
        )
        self.assertTrue(result.ok, result.message)
