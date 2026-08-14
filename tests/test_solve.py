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
from tools.baseline import (
    instance_for,
    iter_corruptions,
    pin_assignment,
    unencoded_clues,
    _output_var_names,
)
from tools.uniqueness import uniqueness_program


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


class PuzzleUniqueTests(unittest.TestCase):
    def test_unique_flag_is_unique(self) -> None:
        for puzzle, case, timeout in iter_cases():
            name = case.get("name", "")
            with self.subTest(puzzle=puzzle, case=name, check="unique"):
                if not case.get("unique"):
                    self.skipTest("unique not declared")
                if not case.get("answer"):
                    self.skipTest("no answer")
                if unencoded_clues(puzzle):
                    self.skipTest("partial encoding")
                spec = load_spec(puzzle)
                inst = Instance.from_json(instance_payload(puzzle, case, with_answer=False))
                names = _output_var_names(spec)
                if not names:
                    self.skipTest("no output variables")
                source = uniqueness_program(spec.source, names)
                result = solve_instance(
                    spec, inst, timeout_ms=timeout, source=source, run_meta=True
                )
                self.assertEqual(
                    result["status"],
                    "sat",
                    f"{puzzle}/{name} uniqueness: "
                    f"{result.get('message', '')[:200]}",
                )


# P0-5: a complete but wrong assignment must be UNSAT. Complements the
# uniqueness check (PuzzleUniqueTests / tests.test_meta). Partial encodings
# (nonempty unencodedClues) warn instead of failing.
REJECT_KEYS = (
    "nurikabe",
    "hitori",
    "slither",
    "sudoku",
    "fillomino",
    "masyu",
    "akari",
    "starbattle",
    "yajilin",
    "kurodoko",
    "context",
    "shikaku",
)


class PuzzleRejectTests(unittest.TestCase):
    def test_wrong_answer_is_rejected(self) -> None:
        timeout = int(os.environ.get("PUZZLE_TIMEOUT_MS", "120000"))
        for puzzle in REJECT_KEYS:
            with self.subTest(puzzle=puzzle, check="reject"):
                spec = load_spec(puzzle)
                instance, case, _source = instance_for(puzzle)
                if instance is None:
                    self.skipTest("no sample or fixture")
                if case is not None and case.get("answer"):
                    assignment = expected_values(case)
                else:
                    result = solve_instance(spec, instance, timeout_ms=timeout)
                    self.assertEqual(
                        result["status"],
                        "sat",
                        f"{puzzle} free-solve {result['status']}: "
                        f"{result.get('message', '')[:200]}",
                    )
                    assignment = result.get("values") or {}
                last = "none"
                detail = "no flippable output cell"
                for values, name, key, old, new in iter_corruptions(spec, assignment):
                    pinned = pin_assignment(instance, spec, values)
                    rejected = solve_instance(spec, pinned, timeout_ms=timeout)
                    last = rejected["status"]
                    detail = f"flipped {name}[{key}] {old}->{new}"
                    if last == "unsat":
                        break
                else:
                    if last == "none":
                        self.skipTest(detail)
                    if unencoded_clues(puzzle):
                        print(f"WARNING {puzzle} reject stayed {last} ({detail})")
                        continue
                    self.fail(
                        f"{puzzle} accepted every one-cell corruption "
                        f"(last {last}, {detail})"
                    )


if __name__ == "__main__":
    unittest.main()
