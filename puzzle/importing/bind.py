"""Bind a decoded :class:`LayerBoard` onto a ``PuzzleSpec`` instance."""

from __future__ import annotations

from typing import Any

from puzzle.spec import REGION_VAR, PuzzleSpec

from .board import LayerBoard

SIDES = ("top", "bottom", "left", "right")


def empty_outside(rows: int, cols: int) -> dict[str, list[int]]:
    return {
        "top": [-1] * cols,
        "bottom": [-1] * cols,
        "left": [-1] * rows,
        "right": [-1] * cols,
    }


def bind_instance(
    board: LayerBoard,
    spec: PuzzleSpec,
    *,
    puzzle_key: str | None = None,
) -> dict[str, Any]:
    """Return an instance JSON dict ready for :class:`Instance.from_json`."""

    key = puzzle_key or spec.key
    clues: dict[str, dict[str, int]] = {}
    regions: dict[str, int] = {}
    params: dict[str, Any] = {}
    warnings: list[str] = list(board.warnings)

    defaults = dict(spec.params.get("defaults") or {})
    params.update(defaults)
    params.setdefault("rows", board.rows)
    params.setdefault("cols", board.cols)
    if spec.key in {"skyscrapers", "easyasabc", "doppelblock", "fuzuli"}:
        params["k"] = board.cols
    elif "k" in defaults:
        params["k"] = int(params.get("k") or board.cols)

    used_numbers_for: str | None = None

    if spec.uses_regions:
        if board.regions:
            regions = dict(board.regions)
        else:
            warnings.append("this rule needs regions, but the URL had no room borders")

    for layer in spec.layers:
        if layer.role != "input":
            continue
        if layer.target == "outside":
            outside = empty_outside(board.rows, board.cols)
            for side in (layer.options or {}).get("sides") or SIDES:
                src = board.outside.get(side) or []
                length = board.cols if side in {"top", "bottom"} else board.rows
                arr = [-1] * length
                for i, value in enumerate(src):
                    if i < length and value is not None and int(value) >= 0:
                        arr[i] = int(value)
                outside[side] = arr
                params[side] = arr
            continue
        if layer.var == REGION_VAR or layer.element == "region":
            continue
        if not layer.var:
            continue
        values = _values_for_layer(layer, board, spec, used_numbers_for)
        if layer.element == "number" and values:
            used_numbers_for = layer.var
        if values:
            clues.setdefault(layer.var, {}).update(values)

    # Akari: a numbered wall is also a wall.
    if spec.key == "akari":
        walls = clues.setdefault("w", {})
        for key_cell, _number in (clues.get("n") or {}).items():
            walls[key_cell] = 1

    # Yajilin: an arrow cell with a number is a clue on both layers.
    if spec.key == "yajilin":
        arrows = clues.get("d") or {}
        numbers = clues.get("n") or {}
        for key_cell, arrow in arrows.items():
            numbers.setdefault(key_cell, numbers.get(key_cell, 0))
        clues["n"] = numbers

    instance = {
        "puzzle": key,
        "rows": board.rows,
        "cols": board.cols,
        "clues": clues,
        "regions": regions,
        "params": params,
        "title": board.title or "",
    }
    instance["_warnings"] = warnings
    return instance


def _values_for_layer(
    layer,
    board: LayerBoard,
    spec: PuzzleSpec,
    used_numbers_for: str | None,
) -> dict[str, int]:
    element = layer.element
    var_spec = spec.var_spec(layer.var)
    kind = layer.target
    out: dict[str, int] = {}

    if element == "number":
        if used_numbers_for and used_numbers_for != layer.var:
            # Second number layer: only keep cells that already have an arrow
            # (Yajilin) or that have not been consumed. Prefer unused cells.
            for key, mark in board.cells.items():
                if mark.number is None:
                    continue
                if mark.arrow is None and used_numbers_for:
                    continue
                out[key] = int(mark.number)
            if out:
                return out
        for key, mark in board.cells.items():
            if mark.number is not None:
                out[key] = int(mark.number)
        return out

    if element == "circle":
        for key, mark in board.cells.items():
            if mark.circle:
                out[key] = int(mark.circle)
            elif mark.number is not None and spec.key in {"kurodoko", "kurotto"}:
                # Circled number drawn as a plain number in pzpr.
                pass
        return out

    if element == "shade":
        for key, mark in board.cells.items():
            if mark.shade:
                out[key] = 1
        return out

    if element == "arrow":
        for key, mark in board.cells.items():
            if mark.arrow is not None:
                out[key] = int(mark.arrow)
        return out

    if element == "dot":
        for key, mark in board.edges.items():
            if mark.dot:
                out[key] = int(mark.dot)
        return out

    if element in {"star", "cross", "triangle", "square", "diagonal", "tree", "tent", "ship", "wave", "bulb"}:
        attr = element
        for key, mark in board.cells.items():
            value = getattr(mark, attr, None)
            if value:
                out[key] = int(value)
        return out

    if element == "edgeline":
        for key, mark in board.edges.items():
            if mark.line:
                out[key] = 1
        return out

    if element == "link":
        for key, mark in board.edges.items():
            if mark.link:
                out[key] = 1
        return out

    if var_spec and var_spec.kind.value != kind:
        return out
    return out
