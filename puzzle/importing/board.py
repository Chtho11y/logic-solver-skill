"""Puzzle-agnostic drawing layers decoded from a Penpa+ or puzz.link URL.

This is the intermediate representation *before* binding to a ``PuzzleSpec``.
Penpa is already a stack of Surface / Number / Symbol / Line / LineE marks;
puzz.link boards are flattened onto the same lattices so the binder can map
them onto ``impls/<key>.json`` layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def cell_key(row: int, col: int) -> str:
    return f"{row},{col}"


def edge_key(orient: str, row: int, col: int) -> str:
    return f"{orient},{row},{col}"


@dataclass
class CellMarks:
    shade: int | None = None
    number: int | None = None
    number_text: str = ""
    circle: int | None = None  # 1 white / 2 black / 3 grey
    square: int | None = None
    triangle: int | None = None
    star: int | None = None
    cross: int | None = None
    arrow: int | None = None  # 0-7, same as puzzle.elements
    diagonal: int | None = None
    tree: int | None = None
    tent: int | None = None
    ship: int | None = None
    wave: int | None = None
    bulb: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class EdgeMarks:
    line: int | None = None  # lattice segment (edgeline)
    link: int | None = None  # centre-to-centre (link)
    dot: int | None = None  # 1 white / 2 black
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class LayerBoard:
    """Decoded marks on our cell / edge / outside lattices."""

    rows: int
    cols: int
    title: str = ""
    author: str = ""
    source: str = ""
    tags: list[str] = field(default_factory=list)
    pid: str = ""
    cells: dict[str, CellMarks] = field(default_factory=dict)
    edges: dict[str, EdgeMarks] = field(default_factory=dict)
    regions: dict[str, int] = field(default_factory=dict)
    outside: dict[str, list[int]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def cell(self, row: int, col: int) -> CellMarks:
        key = cell_key(row, col)
        mark = self.cells.get(key)
        if mark is None:
            mark = CellMarks()
            self.cells[key] = mark
        return mark

    def edge(self, orient: str, row: int, col: int) -> EdgeMarks:
        key = edge_key(orient, row, col)
        mark = self.edges.get(key)
        if mark is None:
            mark = EdgeMarks()
            self.edges[key] = mark
        return mark

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def to_layers_json(self) -> list[dict[str, Any]]:
        """Generic layers for the API / UI, independent of a puzzle spec."""

        def collect(
            attr: str,
            from_cells: bool = True,
            *,
            keep_zero: bool = False,
        ) -> dict[str, int]:
            out: dict[str, int] = {}
            items = self.cells.items() if from_cells else self.edges.items()
            for key, mark in items:
                value = getattr(mark, attr, None)
                if value is None or value == "":
                    continue
                if value == 0 and not keep_zero:
                    continue
                out[key] = int(value)
            return out

        layers: list[dict[str, Any]] = []

        def add(layer_id: str, element: str, target: str, values: dict[str, int]) -> None:
            if values:
                layers.append(
                    {"id": layer_id, "element": element, "target": target, "values": values}
                )

        add("surface", "shade", "cell", collect("shade"))
        numbers = {
            key: mark.number
            for key, mark in self.cells.items()
            if mark.number is not None
        }
        add("number", "number", "cell", {k: int(v) for k, v in numbers.items()})
        add("circle", "circle", "cell", collect("circle"))
        add("square", "square", "cell", collect("square"))
        add("triangle", "triangle", "cell", collect("triangle"))
        add("star", "star", "cell", collect("star"))
        add("cross", "cross", "cell", collect("cross"))
        add("arrow", "arrow", "cell", collect("arrow", keep_zero=True))
        add("diagonal", "diagonal", "cell", collect("diagonal"))
        add("tree", "tree", "cell", collect("tree"))
        add("edgeline", "edgeline", "edge", collect("line", from_cells=False))
        add("link", "link", "edge", collect("link", from_cells=False))
        add("dot", "dot", "edge", collect("dot", from_cells=False))
        if self.regions:
            layers.append(
                {
                    "id": "regions",
                    "element": "region",
                    "target": "cell",
                    "values": dict(self.regions),
                }
            )
        if any(self.outside.get(side) for side in ("top", "bottom", "left", "right")):
            layers.append(
                {
                    "id": "outside",
                    "element": "outside",
                    "target": "outside",
                    "values": {
                        side: list(values)
                        for side, values in self.outside.items()
                        if values
                    },
                }
            )
        return layers


_CELL_ATTR = {
    "shade": "shade",
    "number": "number",
    "circle": "circle",
    "square": "square",
    "triangle": "triangle",
    "star": "star",
    "cross": "cross",
    "arrow": "arrow",
    "diagonal": "diagonal",
    "tree": "tree",
    "tent": "tent",
    "ship": "ship",
    "wave": "wave",
    "bulb": "bulb",
}

_EDGE_ATTR = {
    "edgeline": "line",
    "link": "link",
    "dot": "dot",
}

_SIDES = ("top", "bottom", "left", "right")


def from_layers_json(rows: int, cols: int, layers: list[dict[str, Any]]) -> LayerBoard:
    """Rebuild a :class:`LayerBoard` from ``to_layers_json`` (or the UI equivalent)."""

    board = LayerBoard(rows=int(rows), cols=int(cols))
    for layer in layers or []:
        element = str(layer.get("element") or layer.get("id") or "")
        if element == "surface":
            element = "shade"
        values = layer.get("values") or {}
        if element in {"region", "regions"}:
            for key, value in values.items():
                try:
                    board.regions[str(key)] = int(value)
                except (TypeError, ValueError):
                    continue
            continue
        if element == "outside":
            for side in _SIDES:
                raw = values.get(side)
                if isinstance(raw, dict):
                    length = cols if side in {"top", "bottom"} else rows
                    arr = [-1] * length
                    for idx, value in raw.items():
                        try:
                            i = int(idx)
                            n = int(value) if not isinstance(value, list) else int(value[0])
                        except (TypeError, ValueError):
                            continue
                        if 0 <= i < length:
                            arr[i] = n
                    board.outside[side] = arr
                elif isinstance(raw, list):
                    board.outside[side] = [
                        int(v) if v is not None and v != "" else -1 for v in raw
                    ]
            continue
        if element in _CELL_ATTR:
            attr = _CELL_ATTR[element]
            if not isinstance(values, dict):
                continue
            for key, value in values.items():
                parts = str(key).split(",")
                if len(parts) != 2:
                    continue
                try:
                    row, col = int(parts[0]), int(parts[1])
                    number = int(value)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    continue
                if not board.in_bounds(row, col):
                    continue
                setattr(board.cell(row, col), attr, number)
            continue
        if element in _EDGE_ATTR:
            attr = _EDGE_ATTR[element]
            if not isinstance(values, dict):
                continue
            for key, value in values.items():
                parts = str(key).split(",")
                if len(parts) != 3:
                    continue
                try:
                    orient, row, col = parts[0], int(parts[1]), int(parts[2])
                    number = int(value)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    continue
                if orient not in {"H", "V"}:
                    continue
                setattr(board.edge(orient, row, col), attr, number)
    return board


def regions_from_walls(rows: int, cols: int, walls: set[str]) -> dict[str, int]:
    """Union-find cells that are not separated by a lattice wall."""

    parent = {cell_key(r, c): cell_key(r, c) for r in range(rows) for c in range(cols)}

    def find(key: str) -> str:
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for row in range(rows):
        for col in range(cols):
            here = cell_key(row, col)
            if col + 1 < cols and edge_key("V", row, col + 1) not in walls:
                union(here, cell_key(row, col + 1))
            if row + 1 < rows and edge_key("H", row + 1, col) not in walls:
                union(here, cell_key(row + 1, col))

    roots: dict[str, int] = {}
    out: dict[str, int] = {}
    next_id = 0
    for row in range(rows):
        for col in range(cols):
            key = cell_key(row, col)
            root = find(key)
            if root not in roots:
                roots[root] = next_id
                next_id += 1
            out[key] = roots[root]
    return out
