"""Solve-and-compare tests driven by ``tests/cases/*.json`` fixtures.

Each fixture is a puzzle instance (the *board*) plus an expected assignment of
output variables (the *answer*). Two checks per case:

* **accept** — pin the answer as givens; the encoding must still be SAT
  (not over-constrained).
* **match** — a free solve must reproduce the answer (not under-constrained).
  Only runs when the case sets ``"unique": true``.

    python -m unittest tests.test_solve
"""

from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from puzzle.runner import solve_instance
from puzzle.spec import Instance, load_spec

from tests.puzzles import expected_values, instance_payload, iter_cases


def _solve(puzzle: str, case: dict, timeout_ms: int, *, with_answer: bool = False):
    spec = load_spec(puzzle)
    inst = Instance.from_json(instance_payload(puzzle, case, with_answer=with_answer))
    return solve_instance(spec, inst, timeout_ms=timeout_ms)


def _dump(values: dict[str, int], rows: int, cols: int) -> str:
    lines = []
    for row in range(rows):
        cells = []
        for col in range(cols):
            value = values.get(f"{row},{col}")
            if value is None:
                cells.append("?")
            elif value == 1:
                cells.append("#")
            elif value == 0:
                cells.append(".")
            else:
                cells.append(str(value))
        lines.append("  " + " ".join(cells))
    return "\n".join(lines)


class PuzzleFixtureTests(unittest.TestCase):
    def test_answer_is_accepted(self) -> None:
        for puzzle, case, timeout in iter_cases():
            name = case.get("name", "")
            with self.subTest(puzzle=puzzle, case=name, check="accept"):
                if not case.get("answer"):
                    self.skipTest("no answer")
                result = _solve(puzzle, case, timeout, with_answer=True)
                self.assertEqual(
                    result["status"],
                    "sat",
                    f"{puzzle}/{name} rejects its own answer: "
                    f"{result.get('message', '')[:200]}",
                )

    def test_solve_matches_answer(self) -> None:
        for puzzle, case, timeout in iter_cases():
            name = case.get("name", "")
            with self.subTest(puzzle=puzzle, case=name, check="match"):
                if not case.get("answer"):
                    self.skipTest("no answer")
                if not case.get("unique"):
                    self.skipTest("non-unique instance")
                result = _solve(puzzle, case, timeout, with_answer=False)
                self.assertEqual(
                    result["status"],
                    "sat",
                    f"{puzzle}/{name} unsat: {result.get('message', '')[:200]}",
                )
                expected = expected_values(case)
                got = result.get("values") or {}
                for var, want in expected.items():
                    actual = got.get(var) or {}
                    if actual != want:
                        rows, cols = int(case["rows"]), int(case["cols"])
                        self.fail(
                            f"{puzzle}/{name} variable {var!r} differs\n"
                            f"expected:\n{_dump(want, rows, cols)}\n"
                            f"got:\n{_dump(actual, rows, cols)}"
                        )


if __name__ == "__main__":
    unittest.main()
