"""The board geometry used by the DSL compiler.

:class:`Grid` only knows about sizes and the three point lattices; every puzzle
specific notion (regions, clues, colours) lives in :mod:`puzzle.spec`.

UI-independent (no PyQt / no z3 import).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from .models import Point, PointKind


@dataclass(frozen=True)
class Grid:
    rows: int
    cols: int

    def __post_init__(self) -> None:
        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("grid must have positive dimensions")

    # -- lattices -------------------------------------------------------

    def cells(self) -> list[Point]:
        return [(r, c) for r in range(self.rows) for c in range(self.cols)]

    def corners(self) -> list[Point]:
        return [(r, c) for r in range(self.rows + 1) for c in range(self.cols + 1)]

    def edges(self) -> list[Point]:
        out: list[Point] = []
        for r in range(self.rows + 1):
            for c in range(self.cols):
                out.append(("H", r, c))
        for r in range(self.rows):
            for c in range(self.cols + 1):
                out.append(("V", r, c))
        return out

    def points(self, kind: PointKind) -> list[Point]:
        if kind is PointKind.CELL:
            return self.cells()
        if kind is PointKind.CORNER:
            return self.corners()
        return self.edges()

    # -- membership -----------------------------------------------------

    def contains(self, kind: PointKind, point: Point) -> bool:
        try:
            if kind is PointKind.CELL:
                r, c = point  # type: ignore[misc]
                return 0 <= int(r) < self.rows and 0 <= int(c) < self.cols
            if kind is PointKind.CORNER:
                r, c = point  # type: ignore[misc]
                return 0 <= int(r) <= self.rows and 0 <= int(c) <= self.cols
            orient, r, c = point  # type: ignore[misc]
            if orient == "H":
                return 0 <= int(r) <= self.rows and 0 <= int(c) < self.cols
            if orient == "V":
                return 0 <= int(r) < self.rows and 0 <= int(c) <= self.cols
            return False
        except (TypeError, ValueError):
            return False

    def has_cell(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def linear(self, cell: Point) -> int:
        """The linear index ``r * cols + c`` of a cell."""

        r, c = cell  # type: ignore[misc]
        return int(r) * self.cols + int(c)

    def __iter__(self) -> Iterator[Point]:
        return iter(self.cells())
