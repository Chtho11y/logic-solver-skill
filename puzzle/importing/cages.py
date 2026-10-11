"""Decode native Penpa inset-corner cages without inventing missing boundaries."""
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from .board import LayerBoard, cell_key
from .errors import PuzzleImportError

if TYPE_CHECKING:
    from .penpa import PenpaGrid


def corner_position(index: int, grid: PenpaGrid) -> tuple[int, int, int] | None:
    """Return row, column and TL/TR/BL/BR slot for Penpa numberS/cage points."""
    area = grid.real_rows * grid.real_cols
    if not 4 * area <= index < 8 * area:
        return None
    cell, slot = divmod(index, 4)
    kind, pos = grid.decode_index(cell - area)
    return (*pos, slot) if kind == "cell" else None


def _cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a, b, p):
    return _cross(a, b, p) == 0 and min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def _intersects(a, b, c, d):
    ab_c, ab_d, cd_a, cd_b = _cross(a, b, c), _cross(a, b, d), _cross(c, d, a), _cross(c, d, b)
    if ab_c * ab_d < 0 and cd_a * cd_b < 0:
        return True
    return any((_on_segment(a, b, c), _on_segment(a, b, d), _on_segment(c, d, a), _on_segment(c, d, b)))


def _inside(point, polygon):
    x, y = point
    inside = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if _on_segment(a, b, point):
            raise PuzzleImportError("Penpa cage boundary crosses a cell centre; redraw a closed cage around whole cells")
        if (a[1] > y) != (b[1] > y) and x < a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]):
            inside = not inside
    return inside


def _outline_groups(data: dict, grid: PenpaGrid) -> list[set[str]]:
    adjacent: dict[int, set[int]] = defaultdict(set)
    points = {}
    for edge in data:
        try:
            a, b = map(int, str(edge).split(","))
        except (TypeError, ValueError) as exc:
            raise PuzzleImportError("Penpa cage has an invalid segment; use closed cell-corner cage outlines") from exc
        if a == b:
            raise PuzzleImportError("Penpa cage has a zero-length segment")
        for index in (a, b):
            position = corner_position(index, grid)
            if position is None:
                raise PuzzleImportError("Penpa cage contains unsupported points outside cell corners")
            row, col, slot = position
            points[index] = (4 * col + (3 if slot % 2 else 1), 4 * row + (3 if slot >= 2 else 1))
        adjacent[a].add(b)
        adjacent[b].add(a)
    if any(len(neighbours) != 2 for neighbours in adjacent.values()):
        raise PuzzleImportError("Penpa cage outline is open or branched; close each cage before importing")

    remaining = set(adjacent)
    groups = []
    while remaining:
        start = min(remaining)
        path, previous, current = [], None, start
        while current not in path:
            path.append(current)
            following = min(n for n in adjacent[current] if n != previous)
            previous, current = current, following
        if current != start or len(path) < 4:
            raise PuzzleImportError("Penpa cage is not a closed outline")
        remaining.difference_update(path)
        polygon = [points[index] for index in path]
        segments = list(zip(polygon, polygon[1:] + polygon[:1]))
        for i, (a, b) in enumerate(segments):
            for j in range(i + 1, len(segments)):
                if j == i + 1 or (i == 0 and j == len(segments) - 1):
                    continue
                if _intersects(a, b, *segments[j]):
                    raise PuzzleImportError("Penpa cage outline crosses itself; redraw a simple closed cage")
        members = {cell_key(r, c) for r in range(grid.inner_rows) for c in range(grid.inner_cols)
                   if _inside((4 * c + 2, 4 * r + 2), polygon)}
        if not members:
            raise PuzzleImportError("Penpa cage outline does not enclose any complete cells")
        groups.append(members)
    return groups


def decode_cages(board: LayerBoard, grid: PenpaGrid, question: dict) -> None:
    explicit = question.get("killercages") or []
    if not isinstance(explicit, list):
        raise PuzzleImportError("Penpa killercages must be a list of cell groups")
    groups = []
    for group in explicit:
        if not isinstance(group, list):
            raise PuzzleImportError("Penpa cage membership must be a list of cell indices")
        members = set()
        for index in group:
            try:
                kind, position = grid.decode_index(int(index))
            except (TypeError, ValueError) as exc:
                raise PuzzleImportError("Penpa cage contains an invalid cell index") from exc
            if kind != "cell":
                raise PuzzleImportError("Penpa cage contains a cell outside the puzzle grid")
            members.add(cell_key(*position))
        if members:
            groups.append(members)

    outlines = question.get("cage") or {}
    if not isinstance(outlines, dict):
        raise PuzzleImportError("Penpa cage outlines must be an object of segments")
    if outlines:
        recovered = _outline_groups(outlines, grid)
        if groups and {frozenset(g) for g in groups} != {frozenset(g) for g in recovered}:
            raise PuzzleImportError("Penpa cage outlines disagree with saved cage membership; recreate the cages before importing")
        groups = recovered
    for number, members in enumerate(groups):
        if any(key in board.cages for key in members):
            raise PuzzleImportError("Overlapping Penpa cages cannot be represented by one cage-membership variable")
        for key in members:
            board.cages[key] = number

    numbers = question.get("numberS") or {}
    if not isinstance(numbers, dict):
        raise PuzzleImportError("Penpa corner numbers must be an object")
    for raw_index, entry in numbers.items():
        try:
            position = corner_position(int(raw_index), grid)
        except (TypeError, ValueError):
            position = None
        if position is None or position[2] != 0 or not isinstance(entry, list) or not entry:
            board.warnings.append(f"Unsupported Penpa corner clue at {raw_index}: only top-left integer clues are supported")
            continue
        try:
            value = int(str(entry[0]).strip())
        except ValueError:
            board.warnings.append(f"Unsupported Penpa corner clue {entry[0]!r}: use an integer total")
            continue
        board.corner_numbers[cell_key(position[0], position[1])] = value


def encode_cages(board: LayerBoard, grid: PenpaGrid) -> tuple[list[list[int]], dict[str, int]]:
    """Square-grid equivalent of Penpa's cage_for_selection (perimeter + joins)."""
    groups = defaultdict(set)
    for key, group in board.cages.items():
        groups[group].add(tuple(map(int, key.split(','))))
    area = grid.real_rows * grid.real_cols
    outlines = {}

    def point(r, c, slot):
        return 4 * (grid.cell_index(r, c) + area) + slot

    def segment(a, b):
        outlines[f"{min(a, b)},{max(a, b)}"] = 10

    for members in groups.values():
        for r, c in members:
            for dr, dc, a, b in ((-1, 0, 0, 1), (1, 0, 2, 3), (0, -1, 0, 2), (0, 1, 1, 3)):
                if (r + dr, c + dc) not in members:
                    segment(point(r, c, a), point(r, c, b))
            if (r, c + 1) in members:
                if not {(r - 1, c), (r - 1, c + 1)} <= members:
                    segment(point(r, c, 1), point(r, c + 1, 0))
                if not {(r + 1, c), (r + 1, c + 1)} <= members:
                    segment(point(r, c, 3), point(r, c + 1, 2))
            if (r + 1, c) in members:
                if not {(r, c - 1), (r + 1, c - 1)} <= members:
                    segment(point(r, c, 2), point(r + 1, c, 0))
                if not {(r, c + 1), (r + 1, c + 1)} <= members:
                    segment(point(r, c, 3), point(r + 1, c, 1))
    return [[grid.cell_index(r, c) for r, c in sorted(members)] for members in groups.values()], outlines
