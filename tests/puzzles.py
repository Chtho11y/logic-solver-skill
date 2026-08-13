"""Load board+answer fixtures from ``tests/cases/*.json``.

A fixture file looks like::

    {
      "puzzle": "nurikabe",
      "timeoutMs": 120000,
      "cases": [
        {
          "name": "5x5",
          "rows": 5,
          "cols": 5,
          "clues": {"n": ["2 . 2", ". . .", "2 . 2"]},
          "answer": {"x": [".#.", "#.#", ".#."]}
        }
      ]
    }

``clues`` / ``answer`` / ``regions`` values may be a point-key dict
(``{"0,1": 1}``) or an ASCII grid (list of strings). In a grid, ``.`` is empty
for clues and 0 for answers; ``#`` is 1; digits are integer values. Spaces in
a line are optional. Region maps should fill every cell (ids 0-9 can be
written without spaces).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CASES_DIR = Path(__file__).resolve().parent / "cases"


def _cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped:
        return []
    if " " in stripped:
        return stripped.split()
    return list(stripped)


def parse_layer(data: Any, *, blank_is_zero: bool) -> dict[str, int]:
    """Turn a dict or ASCII grid into ``{"r,c": int}``."""

    if data is None:
        return {}
    if isinstance(data, dict):
        return {str(key): int(value) for key, value in data.items()}
    if not isinstance(data, list):
        raise TypeError(f"layer must be a dict or list of strings, got {type(data).__name__}")
    out: dict[str, int] = {}
    for row, line in enumerate(data):
        if not isinstance(line, str):
            raise TypeError("grid rows must be strings")
        for col, token in enumerate(_cells(line)):
            if token in {".", "·", "_"}:
                if blank_is_zero:
                    out[f"{row},{col}"] = 0
                continue
            if token == "#":
                out[f"{row},{col}"] = 1
                continue
            if token == "?":
                continue
            out[f"{row},{col}"] = int(token)
    return out


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_cases(directory: Path | None = None):
    """Yield ``(puzzle, case_dict, timeout_ms)`` for every fixture file."""

    folder = directory or CASES_DIR
    if not folder.is_dir():
        return
    for path in sorted(folder.glob("*.json")):
        data = load_fixture(path)
        puzzle = data.get("puzzle") or path.stem
        timeout = int(data.get("timeoutMs", 120000))
        for case in data.get("cases", ()):
            yield puzzle, case, timeout


def instance_payload(puzzle: str, case: dict, *, with_answer: bool = False) -> dict[str, Any]:
    """Build the JSON instance consumed by :func:`puzzle.runner.solve_instance`."""

    clues = {
        name: parse_layer(layer, blank_is_zero=False)
        for name, layer in (case.get("clues") or {}).items()
    }
    if with_answer:
        for name, layer in (case.get("answer") or {}).items():
            clues[name] = parse_layer(layer, blank_is_zero=True)
    payload: dict[str, Any] = {
        "puzzle": puzzle,
        "rows": int(case["rows"]),
        "cols": int(case["cols"]),
        "clues": clues,
        "regions": parse_layer(case.get("regions") or {}, blank_is_zero=False),
        "params": dict(case.get("params") or {}),
    }
    if case.get("title"):
        payload["title"] = case["title"]
    return payload


def expected_values(case: dict) -> dict[str, dict[str, int]]:
    return {
        name: parse_layer(layer, blank_is_zero=True)
        for name, layer in (case.get("answer") or {}).items()
    }
