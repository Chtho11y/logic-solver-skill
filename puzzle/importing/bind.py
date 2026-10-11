"""Bind a decoded :class:`LayerBoard` onto a ``PuzzleSpec`` instance."""

from __future__ import annotations

from typing import Any

from puzzle.spec import REGION_VAR, PuzzleSpec

from .board import LayerBoard
from .errors import PuzzleImportError

SIDES = ("top", "bottom", "left", "right")


def empty_outside(rows: int, cols: int) -> dict[str, list[int]]:
    return {
        "top": [-1] * cols,
        "bottom": [-1] * cols,
        "left": [-1] * rows,
        "right": [-1] * rows,
    }


def bind_instance(
    board: LayerBoard,
    spec: PuzzleSpec,
    *,
    puzzle_key: str | None = None,
) -> dict[str, Any]:
    """Return an instance JSON dict ready for :class:`Instance.from_json`."""

    key = puzzle_key or spec.key
    clues: dict[str, dict[str, int | list[int]]] = {}
    regions: dict[str, int] = {}
    params: dict[str, Any] = {}
    warnings: list[str] = list(board.warnings)

    defaults = dict(spec.params.get("defaults") or {})
    params.update(defaults)
    params.setdefault("rows", board.rows)
    params.setdefault("cols", board.cols)
    if spec.key == "skyscrapers":
        params["k"] = board.cols

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
                    if i >= length or value is None:
                        continue
                    if (layer.options or {}).get("mode") == "list":
                        runs = value if isinstance(value, list) else [value]
                        arr[i] = [int(v) for v in runs if int(v) >= 0]
                    elif isinstance(value, list):
                        warnings.append(f"{side}[{i}] expects one number, received multiple clues")
                    elif int(value) >= 0:
                        arr[i] = int(value)
                outside[side] = arr
                params[side] = arr
            continue
        if layer.var == REGION_VAR:
            continue
        if not layer.var:
            continue
        values = _values_for_layer(layer, board, spec, used_numbers_for)
        if (layer.element == "number" and values and layer.options.get("semantic") != "cage-total"
                and layer.options.get("importLayer") not in {"cage_totals", "corner_numbers"}
                and layer.options.get("placement") != "corner"):
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
) -> dict[str, int | list[int]]:
    element = layer.element
    var_spec = spec.var_spec(layer.var)
    kind = layer.target
    out: dict[str, int] = {}

    semantic = layer.options.get("semantic")
    imported = layer.options.get("importLayer")
    if element == "region":
        if not var_spec or var_spec.var_type.value != "constant":
            raise PuzzleImportError(f"Region input {layer.var!r} must bind a constant cell variable or a region-partition variable")
        if var_spec.kind.value != "cell":
            raise PuzzleImportError(f"Region input {layer.var!r} must use cell points")
        return dict(board.cages if semantic == "cage-region" or imported == "cage_regions" else board.regions)

    if element == "number":
        if semantic == "cage-total" or imported in {"cage_totals", "corner_numbers"} or layer.options.get("placement") == "corner":
            return dict(board.corner_numbers)
        if layer.options.get("mode") == "list":
            from .clues import parse_run_clue
            return {key: parse_run_clue(mark.number_text or str(mark.number))
                    for key, mark in board.cells.items()
                    if mark.number_text or mark.number is not None}
        if used_numbers_for and used_numbers_for != layer.var and any(mark.number is not None or mark.number_text for mark in board.cells.values()):
            raise PuzzleImportError(f"Number marks match both {used_numbers_for!r} and {layer.var!r}; import into separate variable documents")
        for key, mark in board.cells.items():
            if mark.number is not None:
                out[key] = int(mark.number)
            elif mark.number_text:
                raise PuzzleImportError(f"Number clue {mark.number_text!r} at {key} is not an integer for {layer.var!r}; use a supported list/text clue layer")
        return out

    if element == "text":
        for key, mark in board.cells.items():
            if mark.number is not None:
                out[key] = int(mark.number)
            elif mark.number_text:
                text = mark.number_text.strip().upper()
                if len(text) != 1 or not "A" <= text <= "Z":
                    raise PuzzleImportError(f"Text clue {mark.number_text!r} at {key} must be a single A–Z letter")
                out[key] = ord(text) - ord("A") + 1
        return out

    if element == "circle":
        for key, mark in board.cells.items():
            if mark.circle:
                out[key] = int(mark.circle) - (1 if "0" in (layer.palette or {}) else 0)
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
