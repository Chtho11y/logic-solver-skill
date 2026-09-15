"""Import a Penpa+ or puzz.link URL as layered board data and an instance."""

from __future__ import annotations

from typing import Any

from puzzle.spec import load_spec

from .bind import bind_instance
from .board import LayerBoard, from_layers_json
from .errors import PuzzleImportError
from .penpa import decode_penpa, encode_penpa, looks_like_penpa
from .pids import guess_from_tags, resolve_puzzle_key
from .puzzlink import decode_puzzlink, looks_like_puzzlink, parse_puzzlink

__all__ = [
    "PuzzleImportError",
    "LayerBoard",
    "from_layers_json",
    "decode_penpa",
    "decode_puzzlink",
    "encode_penpa",
    "encode_layers",
    "import_url",
    "looks_like_penpa",
    "looks_like_puzzlink",
    "parse_puzzlink",
    "resolve_puzzle_key",
]


def detect_kind(url: str) -> str:
    if looks_like_penpa(url):
        return "penpa"
    if looks_like_puzzlink(url):
        return "puzzlink"
    raise PuzzleImportError("URL is neither Penpa+ nor puzz.link")


def import_url(url: str, puzzle: str | None = None) -> dict[str, Any]:
    """Decode ``url`` into generic drawing layers, then optionally bind a rule.

Penpa+ is puzzle-agnostic: Surface / Number / Symbol / Line / LineE become a
:class:`LayerBoard` even when no genre tag is present. puzz.link URLs carry a
pid and are flattened onto the same lattices via pzprjs. Binding to
``impls/<key>.json`` happens only when the type is known (pid, Penpa tags, or
the ``puzzle`` hint).

    Returns a JSON-serialisable dict::

        {
          "kind": "penpa" | "puzzlink",
          "puzzle": "nurikabe" | null,
          "instance": {...} | null,
          "layers": [...],
          "warnings": [...],
          "title": "",
          "sourceUrl": "...",
          "pid": "",
        }
    """

    kind = detect_kind(url)
    if kind == "penpa":
        board = decode_penpa(url)
    else:
        board = decode_puzzlink(url)

    warnings = list(board.warnings)
    guessed = board.pid or guess_from_tags(board.tags, board.title)
    forced = resolve_puzzle_key(puzzle) if puzzle else None
    inferred = resolve_puzzle_key(guessed) if guessed else None
    if inferred and forced and inferred != forced:
        warnings.append(f"URL is {inferred}, not the selected {forced}")
    key = inferred or forced
    instance = None
    if key:
        spec = load_spec(key)
        bound = bind_instance(board, spec, puzzle_key=key)
        warnings.extend(bound.pop("_warnings", []))
        instance = bound
    elif guessed:
        warnings.append(f"puzzle {guessed!r} is not implemented; showing generic layers only")
    else:
        warnings.append("could not infer a puzzle type; pick one and import again")

    return {
        "kind": kind,
        "puzzle": key,
        "instance": instance,
        "layers": board.to_layers_json(),
        "warnings": warnings,
        "title": board.title,
        "author": board.author,
        "sourceUrl": board.source or url,
        "pid": board.pid,
        "rows": board.rows,
        "cols": board.cols,
        "tags": board.tags,
    }


def encode_layers(
    rows: int,
    cols: int,
    layers: list[dict[str, Any]] | None = None,
    *,
    title: str = "",
    tags: list[str] | None = None,
) -> str:
    """Turn generic UI layers into a Penpa+ edit URL."""

    board = from_layers_json(int(rows), int(cols), layers or [])
    if title:
        board.title = title
    if tags:
        board.tags = list(tags)
    return encode_penpa(board, title=title, tags=tags)
