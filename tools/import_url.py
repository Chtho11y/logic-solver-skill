"""CLI: decode a Penpa+ or puzz.link URL.

    python -m tools.import_url 'https://puzz.link/p?nurikabe/5/5/g5k2o1k3g'
    python -m tools.import_url --puzzle skyscrapers '<penpa url>'
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from puzzle.importing import PuzzleImportError, import_url  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import a Penpa+ or puzz.link URL")
    parser.add_argument("url", help="full Penpa+ / puzz.link URL, or pid/w/h/body")
    parser.add_argument("--puzzle", help="force an impls/ key (skip genre guessing)")
    parser.add_argument("--json", action="store_true", help="print the full payload")
    args = parser.parse_args(argv)
    try:
        payload = import_url(args.url, puzzle=args.puzzle)
    except PuzzleImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print(f"{payload['kind']}  {payload['rows']}x{payload['cols']}  puzzle={payload['puzzle']!r}")
    if payload.get("title"):
        print(f"title: {payload['title']}")
    print(f"layers: {', '.join(layer['id'] for layer in payload['layers']) or '(none)'}")
    for warning in payload.get("warnings") or []:
        print(f"warning: {warning}")
    instance = payload.get("instance")
    if instance:
        clues = instance.get("clues") or {}
        filled = {name: len(values) for name, values in clues.items() if values}
        print(f"clues: {filled or '{}'}")
        if instance.get("regions"):
            print(f"regions: {len(set(instance['regions'].values()))} rooms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
