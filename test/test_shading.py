"""Regression tests for the shading rules implemented in gen_shade1/2.

For every fully-implemented rule we solve a deliberately complex instance and
then validate the solver's output with the *independent* reference checker in
``test/ref.py`` (a pure-Python reading of the rule text, sharing no code with
the DSL).  This catches DSL encodings that are too weak (they would accept a
board that violates the rule) or too strong (the instance would come out
unsatisfiable).

    python -m unittest discover -s test
"""

from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from puzzle.runner import solve_instance  # noqa: E402
from puzzle.spec import Instance, load_spec  # noqa: E402

from . import ref  # noqa: E402
from .cases import CASES  # noqa: E402


def _board_from_values(values, rows, cols):
    board = {}
    for key, v in values.items():
        if v is None:
            continue
        r, c = map(int, key.split(","))
        board[(r, c)] = int(v)
    return board


class ShadingRuleTests(unittest.TestCase):

    def _solve(self, key, inst, timeout_ms=120000):
        spec = load_spec(key)
        return solve_instance(spec, Instance.from_json(inst), timeout_ms=timeout_ms)

    def test_expected_solutions_pass_reference_checkers(self):
        """The hand-designed expected grids really satisfy the rule (sanity)."""
        for key, inst, grid, note in CASES:
            with self.subTest(key=key):
                errors = ref.CHECKERS[key](grid, inst)
                self.assertEqual(
                    errors, [],
                    f"{key}: expected grid violates the rule: {errors}",
                )

    def test_complex_instances_solve(self):
        """Every complex instance is satisfiable under the DSL encoding."""
        for key, inst, grid, note in CASES:
            with self.subTest(key=key):
                result = self._solve(key, inst)
                self.assertEqual(
                    result["status"], "sat",
                    f"{key} ({note}) unsat: {result.get('message', '')[:120]}",
                )

    def test_solver_output_passes_reference_checkers(self):
        """Whatever the solver returns must be a valid board under the rule."""
        for key, inst, grid, note in CASES:
            with self.subTest(key=key):
                result = self._solve(key, inst)
                if result["status"] != "sat":
                    continue  # covered by the solve test above
                board = _board_from_values(
                    result["values"]["x"], inst["rows"], inst["cols"])
                errors = ref.CHECKERS[key](board, inst)
                self.assertEqual(
                    errors, [],
                    f"{key} ({note}) solver returned a board that violates the rule: "
                    f"{errors}\nboard:\n{_dump(board, inst['rows'], inst['cols'])}",
                )


def _dump(board, rows, cols):
    lines = []
    for r in range(rows):
        lines.append("  " + " ".join("#" if board.get((r, c)) else "." for c in range(cols)))
    return "\n".join(lines)


if __name__ == "__main__":
    unittest.main()
