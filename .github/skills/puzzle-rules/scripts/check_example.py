"""Validate the bundled example without registering it or changing project files.

Run from any directory. --repo can locate the framework if this skill was moved.
This is an example-specific semantic check, not a validator for arbitrary puzzles.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import itertools
import json
from pathlib import Path
import sys

SKILL = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def rule_oracle(bits, instance):
    """Direct counts and BFS, independent of the DSL and its helpers."""
    rows, cols = instance["rows"], instance["cols"]
    values = {(r, c): bits[r * cols + c] for r in range(rows) for c in range(cols)}

    def neighbours(p):
        r, c = p
        return [q for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)) if q in values]

    if any(value and any(values[q] for q in neighbours(p)) for p, value in values.items()):
        return False
    remaining = {p for p, value in values.items() if value == 0}
    if remaining:
        todo = [remaining.pop()]
        while todo:
            for q in neighbours(todo.pop()):
                if q in remaining:
                    remaining.remove(q)
                    todo.append(q)
        if remaining:
            return False
    regions = instance["regions"]
    for rid in set(regions.values()):
        count = sum(values[tuple(map(int, key.split(",")))] for key, region in regions.items() if region == rid)
        if count != instance["params"]["k"]:
            return False
    for key, n in instance["clues"]["n"].items():
        p = tuple(map(int, key.split(",")))
        if values[p] or sum(values[q] for q in neighbours(p)) != n:
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--backend", default="z3", help="Concrete installed backend; no silent auto fallback")
    args = parser.parse_args()
    repo = args.repo or next((p for p in SKILL.parents if (p / "puzzle/spec.py").is_file()), None)
    if repo is None or not (repo / "puzzle/spec.py").is_file():
        parser.error("pass --repo pointing to the Logic Puzzle Studio repository")
    if args.backend == "auto":
        parser.error("select a concrete backend to make validation reproducible")
    sys.path.insert(0, str(repo.resolve()))
    from puzzle.importing.board import LayerBoard
    from puzzle.importing.penpa import encode_penpa
    from puzzle.runner import solve_payload

    folder = SKILL / "assets/room-shade"
    spec = json.loads((folder / "room-shade.json").read_text(encoding="utf-8"))
    source = (folder / "room-shade.dsl").read_text(encoding="utf-8")
    sample = json.loads((folder / "sample.json").read_text(encoding="utf-8"))
    payload = {"spec": {**spec, "source": source}, "source": source,
               "instance": sample, "backend": args.backend, "timeoutMs": 10000}

    def run(request):
        result = solve_payload(request)
        require(result["status"] in {"sat", "unsat"}, str(result))
        require(result.get("backend") == args.backend, "unexpected backend fallback")
        return result

    result = run(payload)
    require(result["status"] == "sat", "example is unsatisfiable")
    answer = result["values"]["x"]
    require(answer == {"0,0": 1, "0,1": 0, "0,2": 0, "1,0": 0, "1,1": 0, "1,2": 1}, "unexpected example answer")
    legal = 0
    for bits in itertools.product((0, 1), repeat=sample["rows"] * sample["cols"]):
        instance = deepcopy(sample)
        instance["clues"]["x"] = {f"{r},{c}": bits[r * sample["cols"] + c]
                                  for r in range(sample["rows"]) for c in range(sample["cols"])}
        expected = rule_oracle(bits, sample)
        actual = run({**payload, "instance": instance})["status"] == "sat"
        require(actual == expected, f"DSL differs from independent rule check: {bits}")
        legal += int(expected)
    require(legal == 1, "example is no longer unique")

    differences = [f"x[cell({key})] != {value}" for key, value in answer.items()]
    blocked = run({**payload, "source": source + "\nany([" + ", ".join(differences) + "])\n"})
    require(blocked["status"] == "unsat", "second solution exists")

    # Exercise the same per-variable documents path as App, including regions.
    numbers = LayerBoard(sample["rows"], sample["cols"])
    for key, value in sample["clues"]["n"].items():
        numbers.cell(*map(int, key.split(","))).number = value
    rooms = LayerBoard(sample["rows"], sample["cols"])
    for col in range(sample["cols"]):
        rooms.edge("H", 1, col).line = 1
    editable = deepcopy(payload["spec"])
    editable["layers"].append({**editable["layers"][-1], "id": "given_answer_x", "role": "input"})
    documents = [{"id": "n", "url": encode_penpa(numbers)},
                 {"id": "x", "url": encode_penpa(LayerBoard(sample["rows"], sample["cols"]))},
                 {"id": "__regions", "url": encode_penpa(rooms)}]
    drawn = run({**payload, "spec": editable, "documents": documents})
    require(drawn["status"] == "sat" and drawn["values"]["x"] == answer, "Penpa document binding changed the answer")
    print(f"PASS ({args.backend}): sample, 64 assignments vs independent oracle, unique output, Penpa document roundtrip")


if __name__ == "__main__":
    main()
