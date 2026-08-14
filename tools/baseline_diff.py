"""Compare two ``docs/baseline/<sha>.json`` snapshots.

Reports accept/free-solve flips, constraint-count rate and time rate.

    python -m tools.baseline_diff docs/baseline/old.json docs/baseline/new.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row["key"]: row for row in data.get("keys", [])}


def _pct(old: float, new: float) -> str:
    if old == 0:
        return "n/a" if new == 0 else "+inf"
    return f"{(new - old) / old * 100:+.1f}%"


def _fmt_row(cells: list[str], widths: list[int]) -> str:
    return "  ".join(cell.ljust(width) for cell, width in zip(cells, widths))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="diff two baseline snapshots")
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument(
        "--min-constraint",
        type=float,
        default=5.0,
        help="only list constraint-rate rows whose |delta| exceeds this percent",
    )
    parser.add_argument(
        "--min-time",
        type=float,
        default=20.0,
        help="only list time-rate rows whose |delta| exceeds this percent",
    )
    args = parser.parse_args(argv)

    old_map = _load(args.old)
    new_map = _load(args.new)
    keys = sorted(set(old_map) | set(new_map))

    flips: list[tuple[str, str, str, str, str]] = []
    constraints: list[tuple[str, str, str, str]] = []
    times: list[tuple[str, str, str, str]] = []

    for key in keys:
        a = old_map.get(key)
        b = new_map.get(key)
        if a is None:
            flips.append((key, "(missing)", "-", "-", "added"))
            continue
        if b is None:
            flips.append((key, a.get("accept", "-"), a.get("free-solve", "-"), "-", "removed"))
            continue
        for field in ("accept", "free-solve"):
            if a.get(field) != b.get(field):
                flips.append((key, str(a.get("accept")), str(a.get("free-solve")),
                              str(b.get("accept")), f"{field}: {a.get(field)} → {b.get(field)}"))
                break
        oc, nc = a.get("constraints"), b.get("constraints")
        if isinstance(oc, (int, float)) and isinstance(nc, (int, float)) and oc:
            rate = abs(nc - oc) / oc * 100
            if rate >= args.min_constraint:
                constraints.append((key, str(oc), str(nc), _pct(oc, nc)))
        ot, nt = a.get("ms"), b.get("ms")
        if isinstance(ot, (int, float)) and isinstance(nt, (int, float)) and ot:
            rate = abs(nt - ot) / ot * 100
            if rate >= args.min_time:
                times.append((key, str(ot), str(nt), _pct(ot, nt)))

    print(f"old: {args.old}")
    print(f"new: {args.new}")
    print(f"keys: {len(old_map)} → {len(new_map)}")
    print()

    print("## accept / free-solve flips")
    if not flips:
        print("(none)")
    else:
        header = ["key", "old accept", "old free", "new accept", "note"]
        rows = [header] + [[*row] for row in flips]
        widths = [max(len(r[i]) for r in rows) for i in range(5)]
        print(_fmt_row(header, widths))
        print(_fmt_row(["-" * w for w in widths], widths))
        for row in flips:
            print(_fmt_row(list(row), widths))
    print()

    print(f"## constraint-count rate (|Δ| ≥ {args.min_constraint:.0f}%)")
    if not constraints:
        print("(none)")
    else:
        header = ["key", "old", "new", "delta"]
        rows = [header] + [list(r) for r in constraints]
        widths = [max(len(r[i]) for r in rows) for i in range(4)]
        print(_fmt_row(header, widths))
        print(_fmt_row(["-" * w for w in widths], widths))
        for row in constraints:
            print(_fmt_row(list(row), widths))
    print()

    print(f"## time rate (|Δ| ≥ {args.min_time:.0f}%)")
    if not times:
        print("(none)")
    else:
        header = ["key", "old ms", "new ms", "delta"]
        rows = [header] + [list(r) for r in times]
        widths = [max(len(r[i]) for r in rows) for i in range(4)]
        print(_fmt_row(header, widths))
        print(_fmt_row(["-" * w for w in widths], widths))
        for row in times:
            print(_fmt_row(list(row), widths))

    return 1 if flips else 0


if __name__ == "__main__":
    raise SystemExit(main())
