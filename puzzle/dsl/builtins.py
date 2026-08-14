"""Predefined functions and constants for the puzzle DSL.

Families of builtins:

* *aggregate* functions consume a whole list (``sum``, ``distinct``, ``all``,
  ``any``, ``max``, ``min``, ``count``);
* *element-wise* functions act on a single element and are mapped over lists
  automatically (``abs``);
* *region producers* build :class:`RegionValue` objects from the grid
  (``row``, ``col``, ``cell``, ``diag``, ``ct_diag``, ``adj4``, ``adj8``,
  ``cell_of``, ``corner_of``, ``edge_of``, ``dir``) plus the ``rows`` / ``cols``
  constant lists and the ``UP`` / ``DOWN`` / ``LEFT`` / ``RIGHT`` direction
  constants.

Each :class:`BuiltinFunction` also carries a human-readable ``signature`` and
``doc`` so the UI can render a browsable function table.

The call context ``ctx`` exposes ``ctx.z3`` (the z3 module) and ``ctx.grid``.
UI-independent (no PyQt import).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..models import Point, PointKind
from .errors import CompileError
from .values import (
    RegionValue,
    VarValue,
    as_bool,
    as_int,
    as_ne,
    as_same,
    flatten_scalars,
    sort_points,
    to_numeric,
)


@dataclass(frozen=True)
class BuiltinFunction:
    name: str
    fn: Callable[..., Any]
    elementwise: bool = False
    # When ``broadcast`` is set, a call with a single ``List[X]`` argument is
    # applied once per element (the function itself only handles a single X).
    broadcast: bool = False
    signature: str = ""
    doc: str = ""
    alias_of: str = ""

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<builtin {self.name}>"


def _as_int(value: Any, name: str) -> int:
    value = to_numeric(value)
    if isinstance(value, bool) or not isinstance(value, int):
        raise CompileError(f"{name} expects a concrete integer argument")
    return value


def _bool_exprs(ctx, values: list) -> list:
    out = []
    for item in values:
        if isinstance(item, bool):
            out.append(ctx.z3.BoolVal(item))
        else:
            out.append(item)
    return out


def _flatten_args(args: list) -> list:
    out: list = []
    for arg in args:
        out.extend(flatten_scalars(arg))
    return out


# -- aggregate functions ------------------------------------------------------


def _fn_sum(ctx, args, pos):
    items = [as_int(item, ctx.z3) for item in _flatten_args(args)]
    if not items:
        return 0
    return ctx.z3.Sum(items)


def _fn_distinct(ctx, args, pos):
    items = _flatten_args(args)
    if any(ctx.z3.is_expr(item) and ctx.z3.is_bool(item) for item in items):
        raise CompileError("distinct() cannot be used on 0/1 boolean variables", pos.line, pos.col)
    if len(items) < 2:
        return ctx.z3.BoolVal(True)
    return ctx.z3.Distinct(items)


def _fn_all(ctx, args, pos):
    items = _bool_exprs(ctx, _flatten_args(args))
    if not items:
        return ctx.z3.BoolVal(True)
    return ctx.z3.And(items)


def _fn_any(ctx, args, pos):
    items = _bool_exprs(ctx, _flatten_args(args))
    if not items:
        return ctx.z3.BoolVal(False)
    return ctx.z3.Or(items)


def _element_count(value: Any) -> int:
    if isinstance(value, RegionValue):
        return len(value.points)
    if isinstance(value, VarValue):
        return len(value.order)
    if isinstance(value, list):
        return sum(_element_count(item) for item in value)
    return 1


def _fn_count(ctx, args, pos):
    return sum(_element_count(arg) for arg in args)


def _pred_bool(ctx, pred, item, pos):
    result = ctx.call(pred, [item], pos)
    return ctx._require_bool(result, pos)


def _fn_count_where(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("count_where(iterable, pred) takes two arguments", pos.line, pos.col)
    items = ctx._iter_items(args[0], pos)
    if not items:
        return 0
    z3 = ctx.z3
    return z3.Sum([z3.If(_pred_bool(ctx, args[1], item, pos), 1, 0) for item in items])


def _fn_sum_where(ctx, args, pos):
    if len(args) != 3:
        raise CompileError(
            "sum_where(iterable, pred, val) takes three arguments", pos.line, pos.col
        )
    items = ctx._iter_items(args[0], pos)
    if not items:
        return 0
    z3 = ctx.z3
    terms = []
    for item in items:
        flag = _pred_bool(ctx, args[1], item, pos)
        value = as_int(ctx.call(args[2], [item], pos), z3)
        terms.append(z3.If(flag, value, 0))
    return z3.Sum(terms)


def _fn_any_where(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("any_where(iterable, pred) takes two arguments", pos.line, pos.col)
    items = ctx._iter_items(args[0], pos)
    if not items:
        return ctx.z3.BoolVal(False)
    return ctx.z3.Or([_pred_bool(ctx, args[1], item, pos) for item in items])


def _fn_all_where(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("all_where(iterable, pred) takes two arguments", pos.line, pos.col)
    items = ctx._iter_items(args[0], pos)
    if not items:
        return ctx.z3.BoolVal(True)
    return ctx.z3.And([_pred_bool(ctx, args[1], item, pos) for item in items])


def _fn_max(ctx, args, pos):
    items = _flatten_args(args)
    if not items:
        raise CompileError("max() of an empty list", pos.line, pos.col)
    acc = items[0]
    for item in items[1:]:
        acc = ctx.z3.If(acc >= item, acc, item)
    return acc


def _fn_min(ctx, args, pos):
    items = _flatten_args(args)
    if not items:
        raise CompileError("min() of an empty list", pos.line, pos.col)
    acc = items[0]
    for item in items[1:]:
        acc = ctx.z3.If(acc <= item, acc, item)
    return acc


# -- element-wise functions ---------------------------------------------------


def _fn_abs(ctx, value):
    if isinstance(value, int):
        return abs(value)
    return ctx.z3.If(value >= 0, value, -value)


# -- debug helpers ------------------------------------------------------------


def _point_str(point: Point) -> str:
    if len(point) == 2:
        return f"({point[0]},{point[1]})"
    return f"{point[0]}({point[1]},{point[2]})"


def _describe_debug(value: Any) -> str:
    """Render a value as the variable/region/list it represents (for print())."""

    if isinstance(value, RegionValue):
        points = ", ".join(_point_str(p) for p in value.points)
        return f"{value.kind.label} region [{len(value.points)}]: {points}"
    if isinstance(value, VarValue):
        points = ", ".join(_point_str(p) for p in value.order)
        return f"variable '{value.name}' ({value.kind.label}) [{len(value.order)}]: {points}"
    if isinstance(value, list):
        return "[" + ", ".join(_describe_debug(item) for item in value) + "]"
    if isinstance(value, bool):
        return str(value)
    return str(value)


def _fn_print(ctx, args, pos):
    """Debug builtin: record a description of each argument during compile.

    Returns an empty list so, used as a statement, it adds no constraint.
    """

    text = " | ".join(_describe_debug(arg) for arg in args) if args else "(empty)"
    ctx.add_debug(pos.line, text)
    return []


# -- geometry helpers ---------------------------------------------------------


def _single_region(value: Any, name: str, pos) -> tuple[PointKind, Point]:
    """Extract the ``(kind, point)`` of a single-point region argument."""

    if isinstance(value, RegionValue) and len(value.points) == 1:
        return value.kind, value.points[0]
    raise CompileError(
        f"{name}() expects a single cell/corner/edge (e.g. cell(0,0))",
        pos.line,
        pos.col,
    )


def _expect_cell(value: Any, name: str, pos) -> Point:
    kind, point = _single_region(value, name, pos)
    if kind is not PointKind.CELL:
        raise CompileError(f"{name}() expects a cell argument", pos.line, pos.col)
    return point


def _cell_in(grid, r: int, c: int) -> bool:
    return 0 <= r < grid.rows and 0 <= c < grid.cols


def _corner_in(grid, r: int, c: int) -> bool:
    return 0 <= r <= grid.rows and 0 <= c <= grid.cols


def _edge_in(grid, orient: str, r: int, c: int) -> bool:
    if orient == "H":
        return 0 <= r <= grid.rows and 0 <= c < grid.cols
    return 0 <= r < grid.rows and 0 <= c <= grid.cols


# -- region producers ---------------------------------------------------------


def _fn_row(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("row(i) takes exactly one argument", pos.line, pos.col)
    index = _as_int(args[0], "row")
    if not 0 <= index < ctx.grid.rows:
        raise CompileError(f"row index {index} out of range", pos.line, pos.col)
    points = [(index, c) for c in range(ctx.grid.cols)]
    return RegionValue.of(PointKind.CELL, points)


def _fn_col(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("col(i) takes exactly one argument", pos.line, pos.col)
    index = _as_int(args[0], "col")
    if not 0 <= index < ctx.grid.cols:
        raise CompileError(f"col index {index} out of range", pos.line, pos.col)
    points = [(r, index) for r in range(ctx.grid.rows)]
    return RegionValue.of(PointKind.CELL, points)


def _fn_cell(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("cell(r, c) takes exactly two arguments", pos.line, pos.col)
    row = _as_int(args[0], "cell")
    col = _as_int(args[1], "cell")
    if not _cell_in(ctx.grid, row, col):
        raise CompileError(f"cell ({row}, {col}) out of range", pos.line, pos.col)
    return RegionValue.of(PointKind.CELL, [(row, col)])


def _fn_corner(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("corner(r, c) takes exactly two arguments", pos.line, pos.col)
    row = _as_int(args[0], "corner")
    col = _as_int(args[1], "corner")
    if not _corner_in(ctx.grid, row, col):
        raise CompileError(f"corner ({row}, {col}) out of range", pos.line, pos.col)
    return RegionValue.of(PointKind.CORNER, [(row, col)])


def _fn_diag(ctx, args, pos):
    if args:
        raise CompileError("diag() takes no arguments", pos.line, pos.col)
    n = min(ctx.grid.rows, ctx.grid.cols)
    return RegionValue.of(PointKind.CELL, [(i, i) for i in range(n)])


def _fn_ct_diag(ctx, args, pos):
    if args:
        raise CompileError("ct_diag() takes no arguments", pos.line, pos.col)
    n = min(ctx.grid.rows, ctx.grid.cols)
    last = ctx.grid.cols - 1
    return RegionValue.of(PointKind.CELL, [(i, last - i) for i in range(n)])


def _fn_adj4(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("adj4(cell) takes exactly one argument", pos.line, pos.col)
    r, c = _expect_cell(args[0], "adj4", pos)
    deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))
    points = [(r + dr, c + dc) for dr, dc in deltas if _cell_in(ctx.grid, r + dr, c + dc)]
    return RegionValue.of(PointKind.CELL, points)


def _fn_adj8(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("adj8(cell) takes exactly one argument", pos.line, pos.col)
    r, c = _expect_cell(args[0], "adj8", pos)
    points = [
        (r + dr, c + dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if (dr, dc) != (0, 0) and _cell_in(ctx.grid, r + dr, c + dc)
    ]
    return RegionValue.of(PointKind.CELL, points)


def _fn_cell_of(ctx, args, pos):
    """Cells directly connected to a cell/corner/edge."""

    if len(args) != 1:
        raise CompileError("cell_of(point) takes exactly one argument", pos.line, pos.col)
    kind, point = _single_region(args[0], "cell_of", pos)
    grid = ctx.grid
    cells: list[Point] = []
    if kind is PointKind.CELL:
        cells = [point]
    elif kind is PointKind.CORNER:
        r, c = point
        cells = [(r + dr, c + dc) for dr in (-1, 0) for dc in (-1, 0)]
    else:  # EDGE
        orient, r, c = point
        if orient == "H":
            cells = [(r - 1, c), (r, c)]
        else:
            cells = [(r, c - 1), (r, c)]
    cells = [(cr, cc) for cr, cc in cells if _cell_in(grid, cr, cc)]
    return RegionValue.of(PointKind.CELL, cells)


def _fn_corner_of(ctx, args, pos):
    """Corners directly connected to a cell/corner/edge."""

    if len(args) != 1:
        raise CompileError("corner_of(point) takes exactly one argument", pos.line, pos.col)
    kind, point = _single_region(args[0], "corner_of", pos)
    grid = ctx.grid
    corners: list[Point] = []
    if kind is PointKind.CELL:
        r, c = point
        corners = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
    elif kind is PointKind.CORNER:
        corners = [point]
    else:  # EDGE -> its two endpoints
        orient, r, c = point
        corners = [(r, c), (r, c + 1)] if orient == "H" else [(r, c), (r + 1, c)]
    corners = [(cr, cc) for cr, cc in corners if _corner_in(grid, cr, cc)]
    return RegionValue.of(PointKind.CORNER, corners)


def _fn_edge_of(ctx, args, pos):
    """Edges directly connected to a cell/corner/edge."""

    if len(args) != 1:
        raise CompileError("edge_of(point) takes exactly one argument", pos.line, pos.col)
    kind, point = _single_region(args[0], "edge_of", pos)
    grid = ctx.grid
    edges: list[Point] = []
    if kind is PointKind.CELL:
        r, c = point
        edges = [("H", r, c), ("H", r + 1, c), ("V", r, c), ("V", r, c + 1)]
    elif kind is PointKind.CORNER:
        r, c = point
        edges = [("H", r, c - 1), ("H", r, c), ("V", r - 1, c), ("V", r, c)]
    else:  # EDGE
        edges = [point]
    edges = [(o, er, ec) for (o, er, ec) in edges if _edge_in(grid, o, er, ec)]
    return RegionValue.of(PointKind.EDGE, edges)


# Direction codes for ``dir(cell, value)``.
DIRECTIONS: dict[int, tuple[int, int]] = {
    0: (-1, 0),   # UP
    1: (1, 0),    # DOWN
    2: (0, -1),   # LEFT
    3: (0, 1),    # RIGHT
    4: (-1, -1),  # UP-LEFT
    5: (-1, 1),   # UP-RIGHT
    6: (1, -1),   # DOWN-LEFT
    7: (1, 1),    # DOWN-RIGHT
}

_OPP = {0: 1, 1: 0, 2: 3, 3: 2, 4: 7, 7: 4, 5: 6, 6: 5}
_ROT90_4 = (0, 3, 1, 2)  # clockwise: UP → RIGHT → DOWN → LEFT


def _fn_dr_of(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("dr_of(d) takes one argument", pos.line, pos.col)
    code = _as_int(args[0], "dr_of")
    if code not in DIRECTIONS:
        raise CompileError("dr_of() direction must be 0-7", pos.line, pos.col)
    return DIRECTIONS[code][0]


def _fn_dc_of(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("dc_of(d) takes one argument", pos.line, pos.col)
    code = _as_int(args[0], "dc_of")
    if code not in DIRECTIONS:
        raise CompileError("dc_of() direction must be 0-7", pos.line, pos.col)
    return DIRECTIONS[code][1]


def _fn_opp(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("opp(d) takes one argument", pos.line, pos.col)
    code = _as_int(args[0], "opp")
    if code not in _OPP:
        raise CompileError("opp() direction must be 0-7", pos.line, pos.col)
    return _OPP[code]


def _fn_rot90(ctx, args, pos):
    if len(args) not in (1, 2):
        raise CompileError("rot90(d [, k]) takes one or two arguments", pos.line, pos.col)
    code = _as_int(args[0], "rot90")
    k = _as_int(args[1], "rot90") if len(args) == 2 else 1
    if code not in (0, 1, 2, 3):
        raise CompileError("rot90() only accepts 4-way directions (0-3)", pos.line, pos.col)
    idx = _ROT90_4.index(code)
    return _ROT90_4[(idx + (k % 4)) % 4]


def _fn_is_horizontal(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("is_horizontal(d) takes one argument", pos.line, pos.col)
    return _as_int(args[0], "is_horizontal") in (2, 3)


def _fn_is_vertical(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("is_vertical(d) takes one argument", pos.line, pos.col)
    return _as_int(args[0], "is_vertical") in (0, 1)


def _fn_tr(ctx, args, pos):
    if len(args) != 3:
        raise CompileError("tr(dr, dc, t) takes three arguments", pos.line, pos.col)
    dr = _as_int(args[0], "tr")
    dc = _as_int(args[1], "tr")
    t = _as_int(args[2], "tr") % 8
    table = (
        (dr, dc),
        (dc, -dr),
        (-dr, -dc),
        (-dc, dr),
        (dr, -dc),
        (-dr, dc),
        (dc, dr),
        (-dc, -dr),
    )
    pair = table[t]
    return [pair[0], pair[1]]


def _fn_line(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("line(axis, i) takes two arguments", pos.line, pos.col)
    axis = _as_int(args[0], "line")
    if axis == 0:
        return _fn_row(ctx, [args[1]], pos)
    if axis == 1:
        return _fn_col(ctx, [args[1]], pos)
    raise CompileError("line() axis must be 0 (row) or 1 (col)", pos.line, pos.col)


def _fn_lines(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("lines(axis) takes one argument", pos.line, pos.col)
    axis = _as_int(args[0], "lines")
    if axis == 0:
        return list(ctx._constants["rows"])
    if axis == 1:
        return list(ctx._constants["cols"])
    raise CompileError("lines() axis must be 0 (row) or 1 (col)", pos.line, pos.col)


def _fn_rev(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("rev(region) takes one argument", pos.line, pos.col)
    value = args[0]
    if isinstance(value, RegionValue):
        return RegionValue(kind=value.kind, points=tuple(reversed(value.points)))
    if isinstance(value, list):
        return list(reversed(value))
    raise CompileError("rev() expects a region or list", pos.line, pos.col)


def _fn_line_from(ctx, args, pos):
    return _fn_dir(ctx, args, pos)


def _fn_side_of(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("side_of(axis, near) takes two arguments", pos.line, pos.col)
    axis = _as_int(args[0], "side_of")
    near = _as_int(args[1], "side_of")
    if axis == 0:
        return "left" if near == 0 else "right"
    if axis == 1:
        return "top" if near == 0 else "bottom"
    raise CompileError("side_of() axis must be 0 (row) or 1 (col)", pos.line, pos.col)


def _fn_dir(ctx, args, pos):
    """All cells from ``cell`` along direction ``value`` (0-7), exclusive."""

    if len(args) != 2:
        raise CompileError("dir(cell, value) takes exactly two arguments", pos.line, pos.col)
    r, c = _expect_cell(args[0], "dir", pos)
    code = _as_int(args[1], "dir")
    if code not in DIRECTIONS:
        raise CompileError("dir() direction must be 0-7 (UP/DOWN/LEFT/RIGHT, ...)", pos.line, pos.col)
    dr, dc = DIRECTIONS[code]
    points: list[Point] = []
    r, c = r + dr, c + dc
    while _cell_in(ctx.grid, r, c):
        points.append((r, c))
        r, c = r + dr, c + dc
    # Keep walk order (do not sort): LEFT/UP rays must start at the nearest cell.
    return RegionValue(kind=PointKind.CELL, points=tuple(points))


def _block(r0: int, c0: int, w: int, h: int) -> RegionValue:
    points = [(r0 + dr, c0 + dc) for dr in range(h) for dc in range(w)]
    return RegionValue.of(PointKind.CELL, points)


def _fn_grid(ctx, args, pos):
    """All non-overlapping ``w`` x ``h`` cell tiles partitioning the grid.

    ``w`` spans columns, ``h`` spans rows. Tiles start at multiples of the tile
    size; only complete tiles that fully fit are returned (a list of regions).
    """

    if len(args) != 2:
        raise CompileError("grid(w, h) takes exactly two arguments", pos.line, pos.col)
    w = _as_int(args[0], "grid")
    h = _as_int(args[1], "grid")
    if w <= 0 or h <= 0:
        raise CompileError("grid(w, h) requires positive dimensions", pos.line, pos.col)
    blocks: list[RegionValue] = []
    for r0 in range(0, ctx.grid.rows, h):
        if r0 + h > ctx.grid.rows:
            break
        for c0 in range(0, ctx.grid.cols, w):
            if c0 + w > ctx.grid.cols:
                break
            blocks.append(_block(r0, c0, w, h))
    return blocks


def _fn_slide(ctx, args, pos):
    """All overlapping ``w`` x ``h`` cell windows (slide step 1).

    ``w`` spans columns, ``h`` spans rows. Every window position where the
    window fully fits is returned (a list of regions); consecutive windows
    overlap.
    """

    if len(args) != 2:
        raise CompileError("slide(w, h) takes exactly two arguments", pos.line, pos.col)
    w = _as_int(args[0], "slide")
    h = _as_int(args[1], "slide")
    if w <= 0 or h <= 0:
        raise CompileError("slide(w, h) requires positive dimensions", pos.line, pos.col)
    windows: list[RegionValue] = []
    for r0 in range(0, ctx.grid.rows - h + 1):
        for c0 in range(0, ctx.grid.cols - w + 1):
            windows.append(_block(r0, c0, w, h))
    return windows


# -- extra geometry -----------------------------------------------------------


def _fn_cells(ctx, args, pos):
    if args:
        raise CompileError("cells() takes no arguments", pos.line, pos.col)
    return RegionValue.of(PointKind.CELL, ctx.grid.cells())


def _fn_spiral(ctx, args, pos):
    """All cells in clockwise spiral order, starting at top-left going right.

    Unlike other region producers this does *not* sort the points: Magic Snail
    needs the visit order.
    """

    if args:
        raise CompileError("spiral() takes no arguments", pos.line, pos.col)
    rows, cols = ctx.grid.rows, ctx.grid.cols
    points: list[Point] = []
    r0, c0, r1, c1 = 0, 0, rows - 1, cols - 1
    while r0 <= r1 and c0 <= c1:
        for c in range(c0, c1 + 1):
            points.append((r0, c))
        r0 += 1
        if r0 > r1:
            break
        for r in range(r0, r1 + 1):
            points.append((r, c1))
        c1 -= 1
        if c0 > c1:
            break
        for c in range(c1, c0 - 1, -1):
            points.append((r1, c))
        r1 -= 1
        if r0 > r1:
            break
        for r in range(r1, r0 - 1, -1):
            points.append((r, c0))
        c0 += 1
    return RegionValue(kind=PointKind.CELL, points=tuple(points))


def _fn_corners(ctx, args, pos):
    if args:
        raise CompileError("corners() takes no arguments", pos.line, pos.col)
    return RegionValue.of(PointKind.CORNER, ctx.grid.corners())


def _fn_edges(ctx, args, pos):
    if args:
        raise CompileError("edges() takes no arguments", pos.line, pos.col)
    return RegionValue.of(PointKind.EDGE, ctx.grid.edges())


def _fn_edge(ctx, args, pos):
    if len(args) != 3:
        raise CompileError('edge("H"|"V", r, c) takes three arguments', pos.line, pos.col)
    orient = args[0]
    if not isinstance(orient, str) or orient.upper() not in ("H", "V"):
        raise CompileError('edge() orientation must be "H" or "V"', pos.line, pos.col)
    r = _as_int(args[1], "edge")
    c = _as_int(args[2], "edge")
    orient = orient.upper()
    if not _edge_in(ctx.grid, orient, r, c):
        raise CompileError(f"edge {orient}({r}, {c}) out of range", pos.line, pos.col)
    return RegionValue.of(PointKind.EDGE, [(orient, r, c)])


def _fn_rect(ctx, args, pos):
    """The cells of the ``h`` x ``w`` rectangle whose top-left is ``(r, c)``."""

    if len(args) != 4:
        raise CompileError("rect(r, c, h, w) takes four arguments", pos.line, pos.col)
    r0 = _as_int(args[0], "rect")
    c0 = _as_int(args[1], "rect")
    h = _as_int(args[2], "rect")
    w = _as_int(args[3], "rect")
    points = [
        (r0 + dr, c0 + dc)
        for dr in range(h)
        for dc in range(w)
        if _cell_in(ctx.grid, r0 + dr, c0 + dc)
    ]
    return RegionValue.of(PointKind.CELL, points)


def _fn_shift(ctx, args, pos):
    """A cell/corner moved by ``(dr, dc)``; an empty region when off-board."""

    if len(args) != 3:
        raise CompileError("shift(point, dr, dc) takes three arguments", pos.line, pos.col)
    kind, point = _single_region(args[0], "shift", pos)
    if kind is PointKind.EDGE:
        raise CompileError("shift() expects a cell or corner", pos.line, pos.col)
    dr = _as_int(args[1], "shift")
    dc = _as_int(args[2], "shift")
    r, c = point[0] + dr, point[1] + dc
    ok = _cell_in(ctx.grid, r, c) if kind is PointKind.CELL else _corner_in(ctx.grid, r, c)
    return RegionValue.of(kind, [(r, c)] if ok else [])


def _fn_diag4(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("diag4(cell) takes exactly one argument", pos.line, pos.col)
    r, c = _expect_cell(args[0], "diag4", pos)
    deltas = ((-1, -1), (-1, 1), (1, -1), (1, 1))
    points = [(r + dr, c + dc) for dr, dc in deltas if _cell_in(ctx.grid, r + dr, c + dc)]
    return RegionValue.of(PointKind.CELL, points)


def _fn_boundary(ctx, args, pos):
    if args:
        raise CompileError("boundary() takes no arguments", pos.line, pos.col)
    g = ctx.grid
    points = [
        (r, c)
        for r in range(g.rows)
        for c in range(g.cols)
        if r in (0, g.rows - 1) or c in (0, g.cols - 1)
    ]
    return RegionValue.of(PointKind.CELL, points)


def _fn_region_of(ctx, args, pos):
    """The user region containing a point (error when it belongs to none)."""

    if len(args) != 1:
        raise CompileError("region_of(point) takes exactly one argument", pos.line, pos.col)
    kind, point = _single_region(args[0], "region_of", pos)
    for region in ctx.region_list:
        if region.kind is kind and point in region.points:
            return region
    raise CompileError(f"no region contains {_point_str(point)}", pos.line, pos.col)


def _fn_region_id(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("region_id(point) takes exactly one argument", pos.line, pos.col)
    kind, point = _single_region(args[0], "region_id", pos)
    for index, region in enumerate(ctx.region_list):
        if region.kind is kind and point in region.points:
            return index
    return -1


def _fn_same_region(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("same_region(a, b) takes two arguments", pos.line, pos.col)
    return _fn_region_id(ctx, [args[0]], pos) == _fn_region_id(ctx, [args[1]], pos)


# -- constants / instance parameters ------------------------------------------


def _wrap_param(value, pos):
    if isinstance(value, (int, bool, str)):
        return value
    if isinstance(value, list):
        return [_wrap_param(item, pos) for item in value]
    if value is None:
        return []
    raise CompileError(f"param value of type {type(value).__name__} is not supported", pos.line, pos.col)


def _fn_param(ctx, args, pos):
    if len(args) != 1 or not isinstance(args[0], str):
        raise CompileError('param("name") takes one string argument', pos.line, pos.col)
    name = args[0]
    if name not in ctx.params:
        raise CompileError(f"no instance parameter named {name!r}", pos.line, pos.col)
    return _wrap_param(ctx.params[name], pos)


def _fn_has_param(ctx, args, pos):
    if len(args) != 1 or not isinstance(args[0], str):
        raise CompileError('has_param("name") takes one string argument', pos.line, pos.col)
    return args[0] in ctx.params


def _fn_is_list(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("is_list(x) takes exactly one argument", pos.line, pos.col)
    return isinstance(args[0], (list, RegionValue, VarValue))


def _fn_defined(ctx, args, pos):
    """The points where a constant variable actually has a value."""

    if len(args) != 1 or not isinstance(args[0], VarValue):
        raise CompileError("defined(var) takes one variable argument", pos.line, pos.col)
    var = args[0]
    return RegionValue.of(var.kind, var.order)


def _fn_has_value(ctx, args, pos):
    if len(args) != 2 or not isinstance(args[0], VarValue):
        raise CompileError("has_value(var, point) takes a variable and a point", pos.line, pos.col)
    var = args[0]
    kind, point = _single_region(args[1], "has_value", pos)
    return kind is var.kind and point in var.quantities


# -- logic / counting helpers -------------------------------------------------


def _fn_ite(ctx, args, pos):
    if len(args) != 3:
        raise CompileError("ite(cond, a, b) takes three arguments", pos.line, pos.col)
    cond = args[0]
    if isinstance(cond, bool):
        return args[1] if cond else args[2]
    return ctx.z3.If(cond, to_numeric(args[1]), to_numeric(args[2]))


def _fn_b2i(ctx, value):
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return value
    return ctx.z3.If(value, 1, 0)


def _fn_count_true(ctx, args, pos):
    items = _bool_exprs(ctx, _flatten_args(args))
    if not items:
        return 0
    return ctx.z3.Sum([ctx.z3.If(item, 1, 0) for item in items])


def _fn_num_eq(ctx, args, pos):
    """How many quantities of ``list`` equal ``value`` (a z3 integer term)."""

    if len(args) != 2:
        raise CompileError("num_eq(list, value) takes two arguments", pos.line, pos.col)
    items = flatten_scalars(args[0])
    value = to_numeric(args[1])
    if not items:
        return 0
    return ctx.z3.Sum([ctx.z3.If(as_bool(item, value, ctx.z3), 1, 0) for item in items])


def _fn_at_most(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("at_most(list, k) takes two arguments", pos.line, pos.col)
    return _fn_count_true(ctx, [args[0]], pos) <= to_numeric(args[1])


def _fn_at_least(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("at_least(list, k) takes two arguments", pos.line, pos.col)
    return _fn_count_true(ctx, [args[0]], pos) >= to_numeric(args[1])


def _fn_exactly(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("exactly(list, k) takes two arguments", pos.line, pos.col)
    return _fn_count_true(ctx, [args[0]], pos) == to_numeric(args[1])


# -- connectivity of equal-valued cells ---------------------------------------

_CC4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CC8 = _CC4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _expect_cell_var(value, name: str, pos) -> VarValue:
    if not isinstance(value, VarValue) or value.kind is not PointKind.CELL:
        raise CompileError(f"{name}() expects a cell variable", pos.line, pos.col)
    return value


def _as_z3_bool_flag(ctx, value):
    if isinstance(value, bool):
        return ctx.z3.BoolVal(value)
    return value


def _encode_is_connected(ctx, var: VarValue, value, deltas) -> Any:
    """L1: at most one same-value component, including the empty set.

    Single-commodity flow. Does **not** build canonical ids and must not share
    the ``valuecc`` memo used by ``cc_*``.
    """

    z3 = ctx.z3
    cells = sort_points(var.order)
    if not cells:
        return z3.BoolVal(True)
    cell_set = set(cells)
    on = {p: _as_z3_bool_flag(ctx, as_bool(var.quantities[p], value, z3)) for p in cells}
    # Supply equals |S|, not |V|: each on-cell consumes 1, so a root that
    # injects n units only conserves when every cell is on.
    k = z3.Sum([z3.If(on[p], 1, 0) for p in cells])
    ok = _new_bool(ctx, "isconn")
    roots = {p: _new_bool(ctx, "isconn#root") for p in cells}
    for p in cells:
        ctx.add_aux(z3.Implies(ok, z3.Implies(roots[p], on[p])))

    flows = {}
    for p in cells:
        r, c = p
        for dr, dc in deltas:
            q = (r + dr, c + dc)
            if q not in cell_set or q <= p:
                continue
            f_pq = ctx.new_int("isconn#f")
            f_qp = ctx.new_int("isconn#f")
            cap = z3.If(z3.And(on[p], on[q]), k, 0)
            for flow in (f_pq, f_qp):
                ctx.add_aux(z3.Implies(ok, flow >= 0))
                ctx.add_aux(z3.Implies(ok, flow <= cap))
            flows[(p, q)] = f_pq
            flows[(q, p)] = f_qp

    any_on = z3.Or(list(on.values()))
    root_sum = z3.Sum([z3.If(roots[p], 1, 0) for p in cells])
    ctx.add_aux(z3.Implies(ok, root_sum <= 1))
    ctx.add_aux(z3.Implies(ok, z3.Implies(any_on, root_sum == 1)))

    for p in cells:
        incoming = []
        outgoing = []
        r, c = p
        for dr, dc in deltas:
            q = (r + dr, c + dc)
            if q not in cell_set:
                continue
            incoming.append(flows[(q, p)])
            outgoing.append(flows[(p, q)])
        inn = z3.Sum(incoming) if incoming else 0
        out = z3.Sum(outgoing) if outgoing else 0
        demand = z3.If(on[p], 1, 0)
        supply = z3.If(roots[p], k, 0)
        ctx.add_aux(z3.Implies(ok, inn - out + supply == demand))
    return ok


def _fn_is_connected(ctx, args, pos, deltas=_CC4, label="is_connected"):
    if len(args) != 2:
        raise CompileError(f"{label}(var, value) takes two arguments", pos.line, pos.col)
    var = _expect_cell_var(args[0], label, pos)
    value = to_numeric(args[1])
    key_val = value if isinstance(value, (int, bool)) else id(value)
    return ctx.memo(
        ("isconn", var.name, key_val, len(deltas)),
        lambda: _encode_is_connected(ctx, var, value, deltas),
    )


def _fn_same_component(ctx, args, pos, deltas=_CC4, label="same_component"):
    if len(args) != 3:
        raise CompileError(f"{label}(var, p, q) takes three arguments", pos.line, pos.col)
    var = _expect_cell_var(args[0], label, pos)
    _kind_p, p = _single_region(args[1], label, pos)
    _kind_q, q = _single_region(args[2], label, pos)
    cc = _value_cc(ctx, var, deltas)
    if p not in cc["id"] or q not in cc["id"]:
        raise CompileError(f"{label}() points must be cells of the variable", pos.line, pos.col)
    return cc["id"][p] == cc["id"][q]


def _fn_is_connected8(ctx, args, pos):
    return _fn_is_connected(ctx, args, pos, _CC8, "is_connected8")


def _build_value_cc(ctx, var: VarValue, deltas, cells=None) -> dict:
    """Encode maximal same-valued connected components of a cell variable.

    Produces per-cell ``id`` (the minimum linear index of the component) plus a
    spanning-tree ``dist`` witness so that *equal id* is equivalent to
    *connected through cells of the same value*.

    When ``cells`` is given, only those points participate: everything else is
    treated as a wall (region-scoped connectivity).
    """

    z3 = ctx.z3
    grid = ctx.grid
    cols = grid.cols
    if cells is None:
        cells = sort_points(var.order)
        tag = f"{var.name}#cc{len(deltas)}"
    else:
        allowed = set(var.order)
        cells = sort_points(p for p in cells if p in allowed)
        ctx._aux_counter += 1
        tag = f"{var.name}#cc{len(deltas)}#in{ctx._aux_counter}"
    cell_set = set(cells)
    ids = {p: z3.Int(f"{tag}#id#r{p[0]}c{p[1]}") for p in cells}
    dist = {p: z3.Int(f"{tag}#d#r{p[0]}c{p[1]}") for p in cells}
    for (r, c) in cells:
        lin = r * cols + c
        idp, dp, xp = ids[(r, c)], dist[(r, c)], var.quantities[(r, c)]
        ctx.add_aux(z3.And(idp >= 0, idp <= lin))
        ctx.add_aux(dp >= 0)
        ctx.add_aux((dp == 0) == (idp == lin))
        neighbours = [(r + dr, c + dc) for dr, dc in deltas if (r + dr, c + dc) in cell_set]
        parents = [
            z3.And(as_same(var.quantities[n], xp, z3), ids[n] == idp, dist[n] == dp - 1)
            for n in neighbours
        ]
        ctx.add_aux(z3.Implies(dp > 0, z3.Or(parents) if parents else z3.BoolVal(False)))
        for n in neighbours:
            ctx.add_aux(z3.Implies(as_same(var.quantities[n], xp, z3), ids[n] == idp))
    return {"id": ids, "dist": dist, "cells": cells, "tag": tag}


def _is_cc_var(ctx, name: str) -> bool:
    check = getattr(ctx, "is_cc_var", None)
    return bool(callable(check) and check(name))


def _wrap_cc_partition(ctx, var: VarValue) -> dict:
    """Reuse the CC variable's own canonical id/dist instead of a second tree."""

    payload = ctx.ensure_cc(var.name)
    cells = sort_points(payload["id"].keys())
    dist = payload.get("dist", payload["_dist"])
    wrapped = {
        "id": payload["id"],
        "dist": dist,
        "cells": cells,
        "tag": f"{var.name}#cc",
        "cc_name": var.name,
        "_payload": payload,
    }
    for key in ("size", "width", "height", "deg", "notch", "full2x2", "corners",
                "row_span", "col_span", "above", "below", "left", "right"):
        if key in payload:
            wrapped[key] = payload[key]
    return wrapped


def _sync_cc_payload(cc: dict, key: str, value) -> None:
    payload = cc.get("_payload")
    if payload is not None:
        payload[key] = value
    cc[key] = value


def _value_cc(ctx, var: VarValue, deltas, region_points=None):
    if region_points is None and _is_cc_var(ctx, var.name):
        if len(deltas) != 4:
            raise CompileError(
                f"8-connectivity builtins do not apply to CC variable '{var.name}'"
            )
        return ctx.memo(
            ("valuecc", var.name, 4, "reused"),
            lambda: _wrap_cc_partition(ctx, var),
        )
    if region_points is None:
        return ctx.memo(("valuecc", var.name, len(deltas)), lambda: _build_value_cc(ctx, var, deltas))
    if _is_cc_var(ctx, var.name) and len(deltas) != 4:
        raise CompileError(
            f"8-connectivity builtins do not apply to CC variable '{var.name}'"
        )
    points = sort_points(region_points)
    return ctx.memo(
        ("valuecc", var.name, len(deltas), points),
        lambda: _build_value_cc(ctx, var, deltas, points),
    )


def _cc_value_value(ctx, var: VarValue, cc: dict, member: str) -> VarValue:
    quantities = cc[member]
    return VarValue(f"{var.name}.{member}", PointKind.CELL, quantities, sort_points(quantities.keys()))


def _make_cc_id(deltas, label: str):
    def fn(ctx, args, pos):
        if len(args) != 1:
            raise CompileError(f"{label}(var) takes exactly one argument", pos.line, pos.col)
        var = _expect_cell_var(args[0], label, pos)
        cc = _value_cc(ctx, var, deltas)
        return _cc_value_value(ctx, var, cc, "id")

    return fn


def _ensure_cc_size(ctx, var: VarValue, deltas, region_points=None) -> dict:
    cc = _value_cc(ctx, var, deltas, region_points)
    if "size" in cc:
        return cc
    if cc.get("cc_name") and region_points is None:
        payload = ctx.ensure_cc_size(cc["cc_name"])
        _sync_cc_payload(cc, "size", payload["size"])
        return cc
    z3 = ctx.z3
    cells = cc["cells"]
    ids = cc["id"]
    tag = cc.get("tag", f"{var.name}#cc{len(deltas)}")
    sizes = {p: z3.Int(f"{tag}#n#r{p[0]}c{p[1]}") for p in cells}
    for p in cells:
        ctx.add_aux(sizes[p] == z3.Sum([z3.If(ids[q] == ids[p], 1, 0) for q in cells]))
    _sync_cc_payload(cc, "size", sizes)
    return cc


def _make_cc_size(deltas, label: str):
    def fn(ctx, args, pos):
        if len(args) != 1:
            raise CompileError(f"{label}(var) takes exactly one argument", pos.line, pos.col)
        var = _expect_cell_var(args[0], label, pos)
        cc = _ensure_cc_size(ctx, var, deltas)
        return _cc_value_value(ctx, var, cc, "size")

    return fn


def _make_cc_count(deltas, label: str):
    def fn(ctx, args, pos):
        """Number of same-valued components whose value equals ``value``."""

        if len(args) != 2:
            raise CompileError(f"{label}(var, value) takes two arguments", pos.line, pos.col)
        var = _expect_cell_var(args[0], label, pos)
        if _is_cc_var(ctx, var.name):
            raise CompileError(
                f"{label}() does not apply to a CC variable; use .size for region area",
                pos.line,
                pos.col,
            )
        value = to_numeric(args[1])
        cc = _value_cc(ctx, var, deltas)
        z3 = ctx.z3
        cols = ctx.grid.cols
        terms = [
            z3.If(z3.And(cc["id"][p] == p[0] * cols + p[1], as_bool(var.quantities[p], value, z3)), 1, 0)
            for p in cc["cells"]
        ]
        return z3.Sum(terms) if terms else 0

    return fn


def _make_cc_root(deltas, label: str):
    def fn(ctx, args, pos):
        if len(args) != 2:
            raise CompileError(f"{label}(var, cell) takes two arguments", pos.line, pos.col)
        var = _expect_cell_var(args[0], label, pos)
        cell = _expect_cell(args[1], label, pos)
        cc = _value_cc(ctx, var, deltas)
        return cc["id"][cell] == cell[0] * ctx.grid.cols + cell[1]

    return fn


def _expect_cell_region(value, name: str, pos) -> RegionValue:
    if not isinstance(value, RegionValue) or value.kind is not PointKind.CELL:
        raise CompileError(f"{name}() expects a cell region", pos.line, pos.col)
    return value


def _make_cc_count_in(deltas, label: str):
    def fn(ctx, args, pos):
        if len(args) != 3:
            raise CompileError(
                f"{label}(var, value, region) takes three arguments", pos.line, pos.col
            )
        var = _expect_cell_var(args[0], label, pos)
        value = to_numeric(args[1])
        region = _expect_cell_region(args[2], label, pos)
        cc = _value_cc(ctx, var, deltas, region.points)
        z3 = ctx.z3
        cols = ctx.grid.cols
        terms = [
            z3.If(z3.And(cc["id"][p] == p[0] * cols + p[1], as_bool(var.quantities[p], value, z3)), 1, 0)
            for p in cc["cells"]
        ]
        return z3.Sum(terms) if terms else 0

    return fn


def _make_cc_size_in(deltas, label: str):
    def fn(ctx, args, pos):
        if len(args) != 3:
            raise CompileError(
                f"{label}(var, cell, region) takes three arguments", pos.line, pos.col
            )
        var = _expect_cell_var(args[0], label, pos)
        cell = _expect_cell(args[1], label, pos)
        region = _expect_cell_region(args[2], label, pos)
        if cell not in set(region.points) or cell not in var.quantities:
            return 0
        cc = _ensure_cc_size(ctx, var, deltas, region.points)
        return cc["size"][cell]

    return fn


def _ensure_cc_bbox(ctx, var: VarValue, deltas) -> dict:
    cc = _ensure_cc_size(ctx, var, deltas)
    if "width" in cc:
        return cc
    z3 = ctx.z3
    cells = cc["cells"]
    ids = cc["id"]
    tag = cc.get("tag", f"{var.name}#cc{len(deltas)}")
    rows, cols = ctx.grid.rows, ctx.grid.cols
    widths = {p: z3.Int(f"{tag}#w#r{p[0]}c{p[1]}") for p in cells}
    heights = {p: z3.Int(f"{tag}#h#r{p[0]}c{p[1]}") for p in cells}
    corners = {p: z3.Int(f"{tag}#cn#r{p[0]}c{p[1]}") for p in cells}
    for p in cells:
        min_r, max_r = rows, -1
        min_c, max_c = cols, -1
        for q in cells:
            same = ids[q] == ids[p]
            min_r = z3.If(z3.And(same, q[0] < min_r), q[0], min_r)
            max_r = z3.If(z3.And(same, q[0] > max_r), q[0], max_r)
            min_c = z3.If(z3.And(same, q[1] < min_c), q[1], min_c)
            max_c = z3.If(z3.And(same, q[1] > max_c), q[1], max_c)
        ctx.add_aux(widths[p] == max_c - min_c + 1)
        ctx.add_aux(heights[p] == max_r - min_r + 1)
        # Same four-corner count as the old DSL (degenerate corners may double-count).
        corner_terms = []
        for q in cells:
            same = ids[q] == ids[p]
            corner_terms.append(z3.If(z3.And(same, q[0] == min_r, q[1] == min_c), 1, 0))
            corner_terms.append(z3.If(z3.And(same, q[0] == min_r, q[1] == max_c), 1, 0))
            corner_terms.append(z3.If(z3.And(same, q[0] == max_r, q[1] == min_c), 1, 0))
            corner_terms.append(z3.If(z3.And(same, q[0] == max_r, q[1] == max_c), 1, 0))
        ctx.add_aux(corners[p] == z3.Sum(corner_terms))
    _sync_cc_payload(cc, "width", widths)
    _sync_cc_payload(cc, "height", heights)
    _sync_cc_payload(cc, "corners", corners)
    return cc


def _make_cc_width(deltas, label: str):
    def fn(ctx, args, pos):
        if len(args) != 1:
            raise CompileError(f"{label}(var) takes exactly one argument", pos.line, pos.col)
        var = _expect_cell_var(args[0], label, pos)
        cc = _ensure_cc_bbox(ctx, var, deltas)
        return _cc_value_value(ctx, var, cc, "width")

    return fn


def _make_cc_height(deltas, label: str):
    def fn(ctx, args, pos):
        if len(args) != 1:
            raise CompileError(f"{label}(var) takes exactly one argument", pos.line, pos.col)
        var = _expect_cell_var(args[0], label, pos)
        cc = _ensure_cc_bbox(ctx, var, deltas)
        return _cc_value_value(ctx, var, cc, "height")

    return fn


def _fn_cc_is_rect(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("cc_is_rect(var, cell) takes two arguments", pos.line, pos.col)
    var = _expect_cell_var(args[0], "cc_is_rect", pos)
    cell = _expect_cell(args[1], "cc_is_rect", pos)
    cc = _ensure_cc_bbox(ctx, var, _CC4)
    if cell not in cc["size"]:
        raise CompileError("cc_is_rect() cell is not in the variable", pos.line, pos.col)
    return cc["size"][cell] == cc["width"][cell] * cc["height"][cell]


def _ensure_cc_deg(ctx, var: VarValue, deltas) -> dict:
    cc = _value_cc(ctx, var, deltas)
    if "deg" in cc:
        return cc
    z3 = ctx.z3
    cells = cc["cells"]
    cell_set = set(cells)
    ids = cc["id"]
    tag = cc.get("tag", f"{var.name}#cc{len(deltas)}")
    degs = {p: z3.Int(f"{tag}#deg#r{p[0]}c{p[1]}") for p in cells}
    for r, c in cells:
        p = (r, c)
        nbs = [(r + dr, c + dc) for dr, dc in deltas if (r + dr, c + dc) in cell_set]
        total = z3.Sum([z3.If(ids[q] == ids[p], 1, 0) for q in nbs]) if nbs else 0
        ctx.add_aux(degs[p] == total)
    _sync_cc_payload(cc, "deg", degs)
    return cc


def _ensure_cc_line(ctx, var: VarValue, deltas) -> dict:
    cc = _value_cc(ctx, var, deltas)
    if "row_span" in cc:
        return cc
    z3 = ctx.z3
    cells = cc["cells"]
    ids = cc["id"]
    tag = cc.get("tag", f"{var.name}#cc{len(deltas)}")
    row_span = {p: z3.Int(f"{tag}#rs#r{p[0]}c{p[1]}") for p in cells}
    col_span = {p: z3.Int(f"{tag}#cs#r{p[0]}c{p[1]}") for p in cells}
    for p in cells:
        ctx.add_aux(row_span[p] == z3.Sum(
            [z3.If(z3.And(ids[q] == ids[p], q[0] == p[0]), 1, 0) for q in cells]
        ))
        ctx.add_aux(col_span[p] == z3.Sum(
            [z3.If(z3.And(ids[q] == ids[p], q[1] == p[1]), 1, 0) for q in cells]
        ))
    _sync_cc_payload(cc, "row_span", row_span)
    _sync_cc_payload(cc, "col_span", col_span)
    return cc


def _ensure_cc_half(ctx, var: VarValue, deltas) -> dict:
    cc = _value_cc(ctx, var, deltas)
    if "above" in cc:
        return cc
    z3 = ctx.z3
    cells = cc["cells"]
    ids = cc["id"]
    tag = cc.get("tag", f"{var.name}#cc{len(deltas)}")
    maps = {}
    specs = (
        ("above", lambda q, p: q[0] < p[0]),
        ("below", lambda q, p: q[0] > p[0]),
        ("left", lambda q, p: q[1] < p[1]),
        ("right", lambda q, p: q[1] > p[1]),
    )
    for name, pred in specs:
        table = {p: z3.Int(f"{tag}#{name[0]}#r{p[0]}c{p[1]}") for p in cells}
        for p in cells:
            ctx.add_aux(table[p] == z3.Sum(
                [z3.If(z3.And(ids[q] == ids[p], pred(q, p)), 1, 0) for q in cells]
            ))
        maps[name] = table
        _sync_cc_payload(cc, name, table)
    return cc


def _ensure_cc_windows(ctx, var: VarValue, deltas) -> dict:
    cc = _value_cc(ctx, var, deltas)
    if "notch" in cc:
        return cc
    z3 = ctx.z3
    cells = cc["cells"]
    cell_set = set(cells)
    ids = cc["id"]
    tag = cc.get("tag", f"{var.name}#cc{len(deltas)}")
    rows, cols = ctx.grid.rows, ctx.grid.cols
    windows = []
    for r in range(rows - 1):
        for c in range(cols - 1):
            window = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            if all(p in cell_set for p in window):
                windows.append(window)
    notches = {p: z3.Int(f"{tag}#n3#r{p[0]}c{p[1]}") for p in cells}
    fulls = {p: z3.Int(f"{tag}#f4#r{p[0]}c{p[1]}") for p in cells}
    for p in cells:
        n_terms = []
        f_terms = []
        for window in windows:
            total = z3.Sum([z3.If(ids[q] == ids[p], 1, 0) for q in window])
            n_terms.append(z3.If(total == 3, 1, 0))
            f_terms.append(z3.If(total == 4, 1, 0))
        ctx.add_aux(notches[p] == (z3.Sum(n_terms) if n_terms else 0))
        ctx.add_aux(fulls[p] == (z3.Sum(f_terms) if f_terms else 0))
    _sync_cc_payload(cc, "notch", notches)
    _sync_cc_payload(cc, "full2x2", fulls)
    return cc


def _cc_deg_count_at(ctx, var: VarValue, deltas, cell, degree):
    cc = _ensure_cc_deg(ctx, var, deltas)
    z3 = ctx.z3
    key = f"deg_count_{degree}"
    if key not in cc:
        cells = cc["cells"]
        ids = cc["id"]
        degs = cc["deg"]
        tag = cc.get("tag", f"{var.name}#cc{len(deltas)}")
        table = {p: z3.Int(f"{tag}#dc{degree}#r{p[0]}c{p[1]}") for p in cells}
        for p in cells:
            ctx.add_aux(table[p] == z3.Sum(
                [z3.If(z3.And(ids[q] == ids[p], degs[q] == degree), 1, 0) for q in cells]
            ))
        _sync_cc_payload(cc, key, table)
    table = cc[key]
    if cell not in table:
        raise CompileError("cc_deg_count() cell is not in the variable")
    return table[cell]


def _fn_cc_corner_count(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("cc_corner_count(var, cell) takes two arguments", pos.line, pos.col)
    var = _expect_cell_var(args[0], "cc_corner_count", pos)
    cell = _expect_cell(args[1], "cc_corner_count", pos)
    cc = _ensure_cc_bbox(ctx, var, _CC4)
    if cell not in cc["corners"]:
        raise CompileError("cc_corner_count() cell is not in the variable", pos.line, pos.col)
    return cc["corners"][cell]


def _fn_cc_notch_count(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("cc_notch_count(var, cell) takes two arguments", pos.line, pos.col)
    var = _expect_cell_var(args[0], "cc_notch_count", pos)
    cell = _expect_cell(args[1], "cc_notch_count", pos)
    cc = _ensure_cc_windows(ctx, var, _CC4)
    if cell not in cc["notch"]:
        raise CompileError("cc_notch_count() cell is not in the variable", pos.line, pos.col)
    return cc["notch"][cell]


def _fn_cc_full2x2(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("cc_full2x2(var, cell) takes two arguments", pos.line, pos.col)
    var = _expect_cell_var(args[0], "cc_full2x2", pos)
    cell = _expect_cell(args[1], "cc_full2x2", pos)
    cc = _ensure_cc_windows(ctx, var, _CC4)
    if cell not in cc["full2x2"]:
        raise CompileError("cc_full2x2() cell is not in the variable", pos.line, pos.col)
    return cc["full2x2"][cell]


def _fn_cc_deg_count(ctx, args, pos):
    if len(args) != 3:
        raise CompileError("cc_deg_count(var, cell, d) takes three arguments", pos.line, pos.col)
    var = _expect_cell_var(args[0], "cc_deg_count", pos)
    cell = _expect_cell(args[1], "cc_deg_count", pos)
    degree = _as_int(args[2], "cc_deg_count")
    if degree < 0 or degree > 4:
        raise CompileError("cc_deg_count() degree must be 0..4", pos.line, pos.col)
    return _cc_deg_count_at(ctx, var, _CC4, cell, degree)


def _fn_cc_half_count(ctx, args, pos):
    if len(args) != 4:
        raise CompileError(
            "cc_half_count(var, cell, axis, side) takes four arguments", pos.line, pos.col
        )
    var = _expect_cell_var(args[0], "cc_half_count", pos)
    cell = _expect_cell(args[1], "cc_half_count", pos)
    axis = _as_int(args[2], "cc_half_count")
    side = _as_int(args[3], "cc_half_count")
    if axis not in (0, 1) or side not in (0, 1):
        raise CompileError("cc_half_count() axis/side must be 0 or 1", pos.line, pos.col)
    cc = _ensure_cc_half(ctx, var, _CC4)
    name = (("above", "below"), ("left", "right"))[axis][side]
    if cell not in cc[name]:
        raise CompileError("cc_half_count() cell is not in the variable", pos.line, pos.col)
    return cc[name][cell]


def _fn_cc_line_count(ctx, args, pos):
    if len(args) != 3:
        raise CompileError("cc_line_count(var, cell, axis) takes three arguments", pos.line, pos.col)
    var = _expect_cell_var(args[0], "cc_line_count", pos)
    cell = _expect_cell(args[1], "cc_line_count", pos)
    axis = _as_int(args[2], "cc_line_count")
    if axis not in (0, 1):
        raise CompileError("cc_line_count() axis must be 0 (row) or 1 (col)", pos.line, pos.col)
    cc = _ensure_cc_line(ctx, var, _CC4)
    table = cc["row_span"] if axis == 0 else cc["col_span"]
    if cell not in table:
        raise CompileError("cc_line_count() cell is not in the variable", pos.line, pos.col)
    return table[cell]


# -- gravity / covering (Stostone) --------------------------------------------

def _fn_drop_covers(ctx, args, pos):
    """Each black 4-component falls as a rigid body; images fill rows ``start..``."""

    if len(args) != 2:
        raise CompileError("drop_covers(var, start_row) takes two arguments", pos.line, pos.col)
    var = _expect_cell_var(args[0], "drop_covers", pos)
    start = _as_int(args[1], "drop_covers")
    z3 = ctx.z3
    grid = ctx.grid
    rows, cols = grid.rows, grid.cols
    if not 0 <= start <= rows:
        raise CompileError(f"drop_covers start_row {start} out of range", pos.line, pos.col)
    cc = _value_cc(ctx, var, _CC4)
    cells = cc["cells"]
    ids = cc["id"]
    drop = ctx.memo(("drop", var.name), lambda: {
        p: z3.Int(f"{var.name}#drop#r{p[0]}c{p[1]}") for p in cells
    })
    parts = []
    for p in cells:
        ctx.add_aux(drop[p] >= 0)
        ctx.add_aux(drop[p] <= max(0, rows - 1 - p[0]))
        parts.append(z3.Implies(as_ne(var.quantities[p], 1, z3), drop[p] == 0))
    for p in cells:
        for q in cells:
            if p < q:
                parts.append(z3.Implies(ids[p] == ids[q], drop[p] == drop[q]))
    by_col: dict[int, list[Point]] = {}
    for p in cells:
        by_col.setdefault(p[1], []).append(p)
    for col, column in by_col.items():
        column.sort()
        for i, p in enumerate(column):
            for q in column[i + 1:]:
                both = z3.And(as_bool(var.quantities[p], 1, z3), as_bool(var.quantities[q], 1, z3))
                parts.append(z3.Implies(both, p[0] + drop[p] < q[0] + drop[q]))
        for dest_r in range(rows):
            hits = [
                z3.If(z3.And(as_bool(var.quantities[p], 1, z3), p[0] + drop[p] == dest_r), 1, 0)
                for p in column
            ]
            total = z3.Sum(hits) if hits else 0
            parts.append(total == (1 if dest_r >= start else 0))
    return z3.And(parts) if parts else z3.BoolVal(True)


# -- loops on the corner / cell lattice ---------------------------------------


def _fn_row_of(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("row_of(point) takes exactly one argument", pos.line, pos.col)
    kind, point = _single_region(args[0], "row_of", pos)
    return int(point[1] if kind is PointKind.EDGE else point[0])


def _fn_col_of(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("col_of(point) takes exactly one argument", pos.line, pos.col)
    kind, point = _single_region(args[0], "col_of", pos)
    return int(point[2] if kind is PointKind.EDGE else point[1])


def _fn_at(ctx, args, pos):
    """The single quantity of ``var`` at a single point (unwraps the list)."""

    if len(args) != 2 or not isinstance(args[0], VarValue):
        raise CompileError("at(var, point) takes a variable and a single point", pos.line, pos.col)
    var = args[0]
    kind, point = _single_region(args[1], "at", pos)
    if kind is not var.kind:
        raise CompileError(
            f"variable '{var.name}' is bound to {var.kind.label} but indexed by a {kind.label}",
            pos.line,
            pos.col,
        )
    if point not in var.quantities:
        raise CompileError(
            f"'{var.name}' has no value at {_point_str(point)}", pos.line, pos.col
        )
    return var.quantities[point]


def _lookup_or_default(var: VarValue, kind: PointKind, point, default):
    if kind is not var.kind or point not in var.quantities:
        return default
    return var.quantities[point]


def _fn_at_or(ctx, args, pos):
    if len(args) != 3 or not isinstance(args[0], VarValue):
        raise CompileError(
            "at_or(var, point, default) takes a variable, a point and a default",
            pos.line,
            pos.col,
        )
    var, point_val, default = args
    if isinstance(point_val, RegionValue) and len(point_val.points) == 0:
        return default
    kind, point = _single_region(point_val, "at_or", pos)
    return _lookup_or_default(var, kind, point, default)


def _fn_nb(ctx, args, pos):
    if len(args) not in (3, 4) or not isinstance(args[0], VarValue):
        raise CompileError(
            "nb(var, point, d [, default]) takes a variable, a point and a direction",
            pos.line,
            pos.col,
        )
    default = args[3] if len(args) == 4 else 0
    code = _as_int(args[2], "nb")
    if code not in DIRECTIONS:
        raise CompileError("nb() direction must be 0-7", pos.line, pos.col)
    dr, dc = DIRECTIONS[code]
    return _fn_nb_at(ctx, [args[0], args[1], dr, dc, default], pos)


def _fn_nb_at(ctx, args, pos):
    if len(args) not in (4, 5) or not isinstance(args[0], VarValue):
        raise CompileError(
            "nb_at(var, point, dr, dc [, default]) takes a variable, a point and an offset",
            pos.line,
            pos.col,
        )
    default = args[4] if len(args) == 5 else 0
    if isinstance(args[1], RegionValue) and len(args[1].points) == 0:
        return default
    kind, point = _single_region(args[1], "nb_at", pos)
    if kind is PointKind.EDGE:
        raise CompileError("nb_at() expects a cell or corner", pos.line, pos.col)
    dr = _as_int(args[2], "nb_at")
    dc = _as_int(args[3], "nb_at")
    r, c = point[0] + dr, point[1] + dc
    ok = _cell_in(ctx.grid, r, c) if kind is PointKind.CELL else _corner_in(ctx.grid, r, c)
    if not ok:
        return default
    return _lookup_or_default(args[0], kind, (r, c), default)


def _fn_in_grid(ctx, args, pos):
    if len(args) not in (1, 3):
        raise CompileError("in_grid(point [, dr, dc]) takes 1 or 3 arguments", pos.line, pos.col)
    if isinstance(args[0], RegionValue) and len(args[0].points) == 0:
        return False
    kind, point = _single_region(args[0], "in_grid", pos)
    dr = _as_int(args[1], "in_grid") if len(args) == 3 else 0
    dc = _as_int(args[2], "in_grid") if len(args) == 3 else 0
    if kind is PointKind.EDGE:
        if dr or dc:
            raise CompileError("in_grid() offset applies to cell/corner", pos.line, pos.col)
        return _edge_in(ctx.grid, point[0], point[1], point[2])
    r, c = point[0] + dr, point[1] + dc
    if kind is PointKind.CELL:
        return _cell_in(ctx.grid, r, c)
    return _corner_in(ctx.grid, r, c)


def _parse_run_clues(raw, name: str, pos) -> list[int]:
    """Parse run-length clues: drop 0, keep positives, keep -1 as ``?``."""

    value = to_numeric(raw)
    if not isinstance(value, list):
        value = [value]
    clues: list[int] = []
    for item in value:
        n = _as_int(item, name)
        if n == 0:
            continue
        if n == -1 or n > 0:
            clues.append(n)
        else:
            raise CompileError(
                f"{name}() length {n} is invalid (use a positive length or -1 for ?)",
                pos.line,
                pos.col,
            )
    return clues


def _as_compile_bool(value: Any, name: str, pos) -> bool:
    if isinstance(value, bool):
        return value
    raise CompileError(f"{name}() extra flag must be a compile-time boolean", pos.line, pos.col)


def _new_bool(ctx, prefix: str):
    ctx._aux_counter += 1
    return ctx.z3.Bool(f"{prefix}#{ctx._aux_counter}")


def _seq_run_slots(ctx, seq: list, circular: bool):
    """Per-index start flags and run lengths of maximal consecutive-1 runs."""

    z3 = ctx.z3
    n = len(seq)
    if n == 0:
        return [], []
    occ = []
    for item in seq:
        if isinstance(item, bool):
            occ.append(z3.BoolVal(item))
        elif isinstance(item, int):
            occ.append(z3.BoolVal(item == 1))
        else:
            occ.append(as_bool(item, 1, z3))

    runlen = [ctx.new_int("run#l") for _ in range(n)]
    is_start = []
    if circular:
        all_one = z3.And(occ) if occ else z3.BoolVal(False)
        ext_occ = occ + occ
        ext_len = [ctx.new_int("run#el") for _ in range(2 * n)]
        ctx.add_aux(ext_len[-1] == z3.If(ext_occ[-1], 1, 0))
        for i in range(2 * n - 2, -1, -1):
            ctx.add_aux(ext_len[i] == z3.If(ext_occ[i], 1 + ext_len[i + 1], 0))
        for j in range(n):
            pred = occ[(j - 1) % n]
            start_j = z3.If(all_one, z3.BoolVal(j == 0), z3.And(occ[j], z3.Not(pred)))
            is_start.append(start_j)
            ctx.add_aux(runlen[j] == z3.If(all_one, n if j == 0 else 0, ext_len[j]))
    else:
        for j in range(n):
            pred_zero = z3.BoolVal(True) if j == 0 else z3.Not(occ[j - 1])
            is_start.append(z3.And(occ[j], pred_zero))
        ctx.add_aux(runlen[-1] == z3.If(occ[-1], 1, 0))
        for j in range(n - 2, -1, -1):
            ctx.add_aux(runlen[j] == z3.If(occ[j], 1 + runlen[j + 1], 0))
    return is_start, runlen


def _match_slots_to_clues(ctx, present, lengths, clues: list[int], extra: bool):
    """Bipartite assignment: clue lengths (with -1 wildcards) vs present slots."""

    z3 = ctx.z3
    if not clues:
        if extra:
            return z3.BoolVal(True)
        parts = [z3.Not(flag) for flag in present]
        return z3.And(parts) if parts else z3.BoolVal(True)
    if not present:
        return z3.BoolVal(False)
    matches = []
    parts = []
    for i, clue in enumerate(clues):
        row = []
        for j, _slot in enumerate(present):
            flag = _new_bool(ctx, "run#m")
            row.append(flag)
            ok_len = z3.BoolVal(True) if clue == -1 else (lengths[j] == clue)
            parts.append(z3.Implies(flag, z3.And(present[j], ok_len)))
        matches.append(row)
        parts.append(z3.Sum([z3.If(flag, 1, 0) for flag in row]) == 1)
    for j, slot in enumerate(present):
        taken = [matches[i][j] for i in range(len(clues))]
        total = z3.Sum([z3.If(flag, 1, 0) for flag in taken])
        parts.append(total <= 1)
        if not extra:
            parts.append(z3.Implies(slot, total == 1))
    return z3.And(parts)


def _fn_runs(ctx, args, pos):
    """The 0/1 sequence's maximal runs of 1 have exactly the given lengths.

    ``lengths`` is an ordered list of concrete integers (typically read from
    ``param(...)``); a single ``0`` means "no filled cell at all". A length of
    ``-1`` is a wildcard (``?``): some run of any positive length.
    """

    if len(args) != 2:
        raise CompileError("runs(list, lengths) takes two arguments", pos.line, pos.col)
    z3 = ctx.z3
    seq = flatten_scalars(args[0])
    lengths = _parse_run_clues(args[1], "runs", pos)
    n = len(seq)
    if not lengths:
        return z3.And([item == 0 for item in seq]) if seq else z3.BoolVal(True)
    min_sum = sum(1 if L == -1 else L for L in lengths)
    if min_sum + len(lengths) - 1 > n:
        return z3.BoolVal(False)
    Li = []
    for L in lengths:
        if L > 0:
            Li.append(L)
        else:
            v = ctx.new_int("runs#L")
            ctx.add_aux(v >= 1)
            ctx.add_aux(v <= n)
            Li.append(v)
    starts = [ctx.new_int("runs#s") for _ in lengths]
    parts = [starts[0] >= 0]
    for i in range(1, len(lengths)):
        parts.append(starts[i] >= starts[i - 1] + Li[i - 1] + 1)
    parts.append(starts[-1] + Li[-1] <= n)
    for j, item in enumerate(seq):
        covered = [z3.And(starts[i] <= j, j < starts[i] + Li[i]) for i in range(len(lengths))]
        parts.append(as_bool(item, 1, z3) == z3.Or(covered))
    return z3.And(parts)


def _fn_runs_set(ctx, args, pos, *, circular: bool = False):
    label = "runs_cycle" if circular else "runs_set"
    if len(args) not in (2, 3):
        raise CompileError(
            f"{label}(list, lengths[, extra]) takes two or three arguments", pos.line, pos.col
        )
    seq = flatten_scalars(args[0])
    clues = _parse_run_clues(args[1], label, pos)
    extra = _as_compile_bool(args[2], label, pos) if len(args) == 3 else False
    z3 = ctx.z3
    if not seq:
        return z3.BoolVal(not clues)
    present, lengths = _seq_run_slots(ctx, seq, circular)
    return _match_slots_to_clues(ctx, present, lengths, clues, extra)


def _fn_runs_cycle(ctx, args, pos):
    """Unordered circular run lengths of a 0/1 ring (Tapa 8-neighbourhood)."""

    return _fn_runs_set(ctx, args, pos, circular=True)


def _fn_values_set(ctx, args, pos):
    """Positive values in ``list`` equal ``lengths`` as a multiset (0 ignored)."""

    if len(args) not in (2, 3):
        raise CompileError(
            "values_set(list, lengths[, extra]) takes two or three arguments", pos.line, pos.col
        )
    items = flatten_scalars(args[0])
    clues = _parse_run_clues(args[1], "values_set", pos)
    extra = _as_compile_bool(args[2], "values_set", pos) if len(args) == 3 else False
    z3 = ctx.z3
    present = []
    lengths = []
    for item in items:
        if isinstance(item, int):
            present.append(z3.BoolVal(item > 0))
            lengths.append(item)
        else:
            present.append(item > 0)
            lengths.append(item)
    return _match_slots_to_clues(ctx, present, lengths, clues, extra)


def _expect_edge_var(value, name: str, pos) -> VarValue:
    if not isinstance(value, VarValue) or value.kind is not PointKind.EDGE:
        raise CompileError(f"{name}() expects an edge variable", pos.line, pos.col)
    return value


def _corner_graph(grid) -> dict:
    """corner -> list of (neighbour corner, edge) pairs."""

    graph: dict = {p: [] for p in grid.corners()}
    for r in range(grid.rows + 1):
        for c in range(grid.cols):
            graph[(r, c)].append(((r, c + 1), ("H", r, c)))
            graph[(r, c + 1)].append(((r, c), ("H", r, c)))
    for r in range(grid.rows):
        for c in range(grid.cols + 1):
            graph[(r, c)].append(((r + 1, c), ("V", r, c)))
            graph[(r + 1, c)].append(((r, c), ("V", r, c)))
    return graph


def _cell_graph(grid) -> tuple[dict, list]:
    """cell -> list of (neighbour cell, edge); plus the list of boundary edges.

    An edge between two cells is the lattice edge that separates them: ``H`` for
    a vertical link, ``V`` for a horizontal one.
    """

    graph: dict = {p: [] for p in grid.cells()}
    outer: list = []
    for edge in grid.edges():
        orient, r, c = edge
        if orient == "H":
            a, b = (r - 1, c), (r, c)
        else:
            a, b = (r, c - 1), (r, c)
        if grid.has_cell(*a) and grid.has_cell(*b):
            graph[a].append((b, edge))
            graph[b].append((a, edge))
        else:
            outer.append(edge)
    return graph, outer


def _fn_deg(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("deg(var, corner) takes two arguments", pos.line, pos.col)
    var = _expect_edge_var(args[0], "deg", pos)
    kind, point = _single_region(args[1], "deg", pos)
    if kind is not PointKind.CORNER:
        raise CompileError("deg() expects a corner", pos.line, pos.col)
    graph = ctx.memo(("cornergraph",), lambda: _corner_graph(ctx.grid))
    return ctx.z3.Sum([as_int(var.quantities[e], ctx.z3) for _, e in graph[point]])


def _fn_cdeg(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("cdeg(var, cell) takes two arguments", pos.line, pos.col)
    var = _expect_edge_var(args[0], "cdeg", pos)
    cell = _expect_cell(args[1], "cdeg", pos)
    graph, _ = ctx.memo(("cellgraph",), lambda: _cell_graph(ctx.grid))
    return ctx.z3.Sum([as_int(var.quantities[e], ctx.z3) for _, e in graph[cell]])


def _link_connect(ctx, var: VarValue, graph: dict, cols_hint: int, tag: str):
    """Single-connected-component encoding for the edges selected by ``var``.

    Returns the z3 boolean "the selected edges form at most/exactly one
    connected component" together with per-node ``used`` expressions.
    """

    z3 = ctx.z3
    nodes = sorted(graph.keys())
    index = {node: i for i, node in enumerate(nodes)}
    ids = {n: ctx.new_int(f"{tag}#id") for n in nodes}
    dist = {n: ctx.new_int(f"{tag}#d") for n in nodes}
    used = {}
    for node in nodes:
        incident = [as_int(var.quantities[e], z3) for _, e in graph[node]]
        used[node] = z3.Sum(incident) > 0 if incident else z3.BoolVal(False)
    for node in nodes:
        lin = index[node]
        idn, dn = ids[node], dist[node]
        ctx.add_aux(z3.And(idn >= 0, idn <= lin))
        ctx.add_aux(dn >= 0)
        ctx.add_aux((dn == 0) == (idn == lin))
        parents = [
            z3.And(as_bool(var.quantities[e], 1, z3), ids[nb] == idn, dist[nb] == dn - 1)
            for nb, e in graph[node]
        ]
        ctx.add_aux(z3.Implies(dn > 0, z3.Or(parents) if parents else z3.BoolVal(False)))
        for nb, e in graph[node]:
            ctx.add_aux(z3.Implies(as_bool(var.quantities[e], 1, z3), ids[nb] == idn))
    roots = z3.Sum([z3.If(z3.And(used[n], dist[n] == 0), 1, 0) for n in nodes])
    return roots, used


def _loop_common(ctx, var, graph, tag, degrees, single):
    z3 = ctx.z3
    key = (tag, var.name)
    roots, _used = ctx.memo(key, lambda: _link_connect(ctx, var, graph, ctx.grid.cols, tag))
    parts = []
    for node, links in graph.items():
        total = z3.Sum([as_int(var.quantities[e], z3) for _, e in links]) if links else 0
        parts.append(z3.Or([total == d for d in degrees]))
    if single:
        parts.append(roots == 1)
    return z3.And(parts)


def _fn_loop(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("loop(var) takes exactly one argument", pos.line, pos.col)
    var = _expect_edge_var(args[0], "loop", pos)
    graph = ctx.memo(("cornergraph",), lambda: _corner_graph(ctx.grid))
    return _loop_common(ctx, var, graph, "loop", (0, 2), True)


def _fn_cloop(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("cloop(var) takes exactly one argument", pos.line, pos.col)
    var = _expect_edge_var(args[0], "cloop", pos)
    graph, outer = ctx.memo(("cellgraph",), lambda: _cell_graph(ctx.grid))
    for edge in outer:
        ctx.add_aux(as_bool(var.quantities[edge], 0, ctx.z3))
    return _loop_common(ctx, var, graph, "cloop", (0, 2), True)


def _fn_connect_edges(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("connect_edges(var) takes exactly one argument", pos.line, pos.col)
    var = _expect_edge_var(args[0], "connect_edges", pos)
    graph = ctx.memo(("cornergraph",), lambda: _corner_graph(ctx.grid))
    roots, _ = ctx.memo(("loop", var.name), lambda: _link_connect(ctx, var, graph, ctx.grid.cols, "loop"))
    return roots == 1


def _fn_connect_links(ctx, args, pos):
    if len(args) != 1:
        raise CompileError("connect_links(var) takes exactly one argument", pos.line, pos.col)
    var = _expect_edge_var(args[0], "connect_links", pos)
    graph, outer = ctx.memo(("cellgraph",), lambda: _cell_graph(ctx.grid))
    for edge in outer:
        ctx.add_aux(as_bool(var.quantities[edge], 0, ctx.z3))
    roots, _ = ctx.memo(("cloop", var.name), lambda: _link_connect(ctx, var, graph, ctx.grid.cols, "cloop"))
    return roots == 1


AGGREGATE_BUILTINS: dict[str, BuiltinFunction] = {
    "sum": BuiltinFunction(
        "sum", _fn_sum, signature="sum(list)", doc="Sum of all quantities in a list/region."
    ),
    "distinct": BuiltinFunction(
        "distinct", _fn_distinct, signature="distinct(list)",
        doc="All quantities must be pairwise different.",
    ),
    "all": BuiltinFunction(
        "all", _fn_all, signature="all(list)", doc="True iff every boolean in the list holds."
    ),
    "any": BuiltinFunction(
        "any", _fn_any, signature="any(list)", doc="True iff at least one boolean holds."
    ),
    "count": BuiltinFunction(
        "count", _fn_count, signature="count(list)", doc="Number of elements (concrete integer)."
    ),
    "count_where": BuiltinFunction(
        "count_where", _fn_count_where, signature="count_where(iterable, pred)",
        doc="Sum If(pred(e), 1, 0) over a region/list. pred is fn or def.",
    ),
    "sum_where": BuiltinFunction(
        "sum_where", _fn_sum_where, signature="sum_where(iterable, pred, val)",
        doc="Sum If(pred(e), val(e), 0) over a region/list.",
    ),
    "any_where": BuiltinFunction(
        "any_where", _fn_any_where, signature="any_where(iterable, pred)",
        doc="Or of pred(e) over a region/list.",
    ),
    "all_where": BuiltinFunction(
        "all_where", _fn_all_where, signature="all_where(iterable, pred)",
        doc="And of pred(e) over a region/list.",
    ),
    "max": BuiltinFunction(
        "max", _fn_max, signature="max(list)", doc="Maximum quantity (z3 If-chain)."
    ),
    "min": BuiltinFunction(
        "min", _fn_min, signature="min(list)", doc="Minimum quantity (z3 If-chain)."
    ),
    "row": BuiltinFunction(
        "row", _fn_row, signature="row(i)", doc="The cells of row i (a region)."
    ),
    "col": BuiltinFunction(
        "col", _fn_col, signature="col(j)", doc="The cells of column j (a region)."
    ),
    "cell": BuiltinFunction(
        "cell", _fn_cell, signature="cell(r, c)", doc="The single cell at (r, c)."
    ),
    "corner": BuiltinFunction(
        "corner", _fn_corner, signature="corner(r, c)", doc="The single corner at (r, c)."
    ),
    "diag": BuiltinFunction(
        "diag", _fn_diag, signature="diag()", doc="Main diagonal cells (0,0),(1,1),..."
    ),
    "ct_diag": BuiltinFunction(
        "ct_diag", _fn_ct_diag, signature="ct_diag()",
        doc="Anti-diagonal cells (0,cols-1),(1,cols-2),...",
    ),
    "adj4": BuiltinFunction(
        "adj4", _fn_adj4, broadcast=True, signature="adj4(cell)",
        doc="The 4 orthogonally adjacent cells (clipped to the grid).",
    ),
    "adj8": BuiltinFunction(
        "adj8", _fn_adj8, broadcast=True, signature="adj8(cell)",
        doc="The 8 surrounding cells (clipped to the grid).",
    ),
    "cell_of": BuiltinFunction(
        "cell_of", _fn_cell_of, broadcast=True, signature="cell_of(point)",
        doc="Cells directly connected to a cell/corner/edge.",
    ),
    "corner_of": BuiltinFunction(
        "corner_of", _fn_corner_of, broadcast=True, signature="corner_of(point)",
        doc="Corners directly connected to a cell/corner/edge.",
    ),
    "edge_of": BuiltinFunction(
        "edge_of", _fn_edge_of, broadcast=True, signature="edge_of(point)",
        doc="Edges directly connected to a cell/corner/edge.",
    ),
    "dir": BuiltinFunction(
        "dir", _fn_dir, signature="dir(cell, value)",
        doc="All cells from a cell along direction value (0-7); use UP/DOWN/LEFT/RIGHT.",
    ),
    "line_from": BuiltinFunction(
        "line_from", _fn_line_from, signature="line_from(p, d)",
        doc="Same as dir(p, d); the line-family name for a ray.",
    ),
    "line": BuiltinFunction(
        "line", _fn_line, signature="line(axis, i)",
        doc="axis 0 = row(i), axis 1 = col(i). Order is left-to-right / top-to-bottom.",
    ),
    "lines": BuiltinFunction(
        "lines", _fn_lines, signature="lines(axis)",
        doc="All rows (axis 0) or all columns (axis 1).",
    ),
    "rev": BuiltinFunction(
        "rev", _fn_rev, signature="rev(region)",
        doc="Reverse a region or list without re-sorting. Do not merge the result with `and`.",
    ),
    "side_of": BuiltinFunction(
        "side_of", _fn_side_of, signature="side_of(axis, near)",
        doc='Outside-clue side name: axis 0 (row) → "left"/"right", axis 1 (col) → "top"/"bottom". near 0 is the start of the line.',
    ),
    "dr_of": BuiltinFunction(
        "dr_of", _fn_dr_of, signature="dr_of(d)", doc="Row offset of direction d (compile-time)."
    ),
    "dc_of": BuiltinFunction(
        "dc_of", _fn_dc_of, signature="dc_of(d)", doc="Column offset of direction d (compile-time)."
    ),
    "opp": BuiltinFunction(
        "opp", _fn_opp, signature="opp(d)", doc="Opposite direction (0↔1, 2↔3, diagonals too)."
    ),
    "rot90": BuiltinFunction(
        "rot90", _fn_rot90, signature="rot90(d [, k])",
        doc="Rotate a 4-way direction clockwise by 90°×k (k defaults to 1).",
    ),
    "is_horizontal": BuiltinFunction(
        "is_horizontal", _fn_is_horizontal, signature="is_horizontal(d)",
        doc="True for LEFT/RIGHT (compile-time).",
    ),
    "is_vertical": BuiltinFunction(
        "is_vertical", _fn_is_vertical, signature="is_vertical(d)",
        doc="True for UP/DOWN (compile-time).",
    ),
    "tr": BuiltinFunction(
        "tr", _fn_tr, signature="tr(dr, dc, t)",
        doc="Dihedral transform t=0..7 of offset (dr, dc); returns [dr', dc'].",
    ),
    "grid": BuiltinFunction(
        "grid", _fn_grid, signature="grid(w, h)",
        doc="List of non-overlapping w×h cell tiles partitioning the board.",
    ),
    "slide": BuiltinFunction(
        "slide", _fn_slide, signature="slide(w, h)",
        doc="List of all overlapping w×h cell windows (sliding step 1).",
    ),
    # -- geometry ------------------------------------------------------
    "cells": BuiltinFunction(
        "cells", _fn_cells, signature="cells()", doc="Every cell of the board (a region)."
    ),
    "spiral": BuiltinFunction(
        "spiral", _fn_spiral, signature="spiral()",
        doc="Every cell in clockwise spiral order from top-left (not sorted).",
    ),
    "corners": BuiltinFunction(
        "corners", _fn_corners, signature="corners()", doc="Every corner of the lattice."
    ),
    "edges": BuiltinFunction(
        "edges", _fn_edges, signature="edges()", doc="Every edge of the lattice."
    ),
    "edge": BuiltinFunction(
        "edge", _fn_edge, signature='edge("H"|"V", r, c)',
        doc='The single edge: "H" above cell (r,c), "V" left of cell (r,c).',
    ),
    "rect": BuiltinFunction(
        "rect", _fn_rect, signature="rect(r, c, h, w)",
        doc="Cells of the h×w rectangle anchored at (r,c) (clipped to the board).",
    ),
    "shift": BuiltinFunction(
        "shift", _fn_shift, broadcast=True, signature="shift(point, dr, dc)",
        doc="A cell/corner moved by (dr,dc); empty region when off-board.",
    ),
    "diag4": BuiltinFunction(
        "diag4", _fn_diag4, broadcast=True, signature="diag4(cell)",
        doc="The 4 diagonally adjacent cells (clipped).",
    ),
    "boundary": BuiltinFunction(
        "boundary", _fn_boundary, signature="boundary()",
        doc="Cells lying on the outer border of the board.",
    ),
    "row_of": BuiltinFunction(
        "row_of", _fn_row_of, broadcast=True, signature="row_of(point)",
        doc="Row index of a cell/corner/edge (compile-time integer).",
    ),
    "col_of": BuiltinFunction(
        "col_of", _fn_col_of, broadcast=True, signature="col_of(point)",
        doc="Column index of a cell/corner/edge (compile-time integer).",
    ),
    "at": BuiltinFunction(
        "at", _fn_at, signature="at(var, point)",
        doc="The single quantity of a variable at one point (unwrapped scalar).",
    ),
    "at_or": BuiltinFunction(
        "at_or", _fn_at_or, signature="at_or(var, point, default)",
        doc="at(var, point) when the point is on-board and has a value, else default.",
    ),
    "nb": BuiltinFunction(
        "nb", _fn_nb, signature="nb(var, point, d [, default])",
        doc="Neighbour of point in direction d; default (0) when off-board.",
    ),
    "nb_at": BuiltinFunction(
        "nb_at", _fn_nb_at, signature="nb_at(var, point, dr, dc [, default])",
        doc="Offset neighbour; default (0) when off-board.",
    ),
    "in_grid": BuiltinFunction(
        "in_grid", _fn_in_grid, signature="in_grid(point [, dr, dc])",
        doc="Compile-time bool: the (optionally offset) point is on the board.",
    ),
    "runs": BuiltinFunction(
        "runs", _fn_runs, signature="runs(list, lengths)",
        doc="The 0/1 sequence's maximal runs of 1 match the ordered lengths. -1 = ? wildcard.",
    ),
    "runs_set": BuiltinFunction(
        "runs_set", _fn_runs_set, signature="runs_set(list, lengths[, extra])",
        doc="Maximal 1-run lengths equal lengths as a multiset. -1 = ?; extra=true allows leftover runs (*).",
    ),
    "runs_cycle": BuiltinFunction(
        "runs_cycle", _fn_runs_cycle, signature="runs_cycle(list, lengths[, extra])",
        doc="Circular unordered run lengths of a 0/1 ring (Tapa 8-neighbourhood). -1 = ?.",
    ),
    "values_set": BuiltinFunction(
        "values_set", _fn_values_set, signature="values_set(list, lengths[, extra])",
        doc="Positive values in the list equal lengths as a multiset (zeros ignored). -1 = ?.",
    ),
    "region_of": BuiltinFunction(
        "region_of", _fn_region_of, broadcast=True, signature="region_of(point)",
        doc="The user-defined region containing a point.",
    ),
    "region_id": BuiltinFunction(
        "region_id", _fn_region_id, broadcast=True, signature="region_id(point)",
        doc="Index of the user region containing a point (-1 if none).",
    ),
    "same_region": BuiltinFunction(
        "same_region", _fn_same_region, signature="same_region(a, b)",
        doc="Whether two points lie in the same user region (compile-time bool).",
    ),
    # -- instance data -------------------------------------------------
    "param": BuiltinFunction(
        "param", _fn_param, signature='param("name")',
        doc="An instance parameter (number or nested list) from the puzzle data.",
    ),
    "has_param": BuiltinFunction(
        "has_param", _fn_has_param, signature='has_param("name")',
        doc="Whether the instance defines that parameter.",
    ),
    "is_list": BuiltinFunction(
        "is_list", _fn_is_list, signature="is_list(x)",
        doc="Whether x is a list/region/variable (compile-time boolean).",
    ),
    "defined": BuiltinFunction(
        "defined", _fn_defined, signature="defined(var)",
        doc="Region of points where a constant variable actually has a value.",
    ),
    "has_value": BuiltinFunction(
        "has_value", _fn_has_value, signature="has_value(var, point)",
        doc="Whether a constant variable has a value at that point (compile-time).",
    ),
    # -- logic / counting ----------------------------------------------
    "ite": BuiltinFunction(
        "ite", _fn_ite, signature="ite(cond, a, b)", doc="If-then-else expression."
    ),
    "count_true": BuiltinFunction(
        "count_true", _fn_count_true, signature="count_true(list)",
        doc="How many booleans in the list hold.",
    ),
    "num_eq": BuiltinFunction(
        "num_eq", _fn_num_eq, signature="num_eq(list, value)",
        doc="How many quantities of the list equal value.",
    ),
    "at_most": BuiltinFunction(
        "at_most", _fn_at_most, signature="at_most(list, k)", doc="At most k booleans hold."
    ),
    "at_least": BuiltinFunction(
        "at_least", _fn_at_least, signature="at_least(list, k)", doc="At least k booleans hold."
    ),
    "exactly": BuiltinFunction(
        "exactly", _fn_exactly, signature="exactly(list, k)", doc="Exactly k booleans hold."
    ),
    # -- connectivity of equal-valued cells (L1–L5; cc_* are aliases) ---
    "is_connected": BuiltinFunction(
        "is_connected", _fn_is_connected, signature="is_connected(var, value)",
        doc="L1: cells holding value form at most one 4-component (empty set counts). Flow encoding; no ids.",
    ),
    "is_connected8": BuiltinFunction(
        "is_connected8", _fn_is_connected8, signature="is_connected8(var, value)",
        doc="L1: at most one 8-connected component of that value (empty set counts).",
    ),
    "component_id": BuiltinFunction(
        "component_id", _make_cc_id(_CC4, "component_id"), signature="component_id(var)",
        doc="L5 (low-level): per-cell canonical id = min r*cols+c in the 4-component.",
    ),
    "cc_id": BuiltinFunction(
        "cc_id", _make_cc_id(_CC4, "cc_id"), signature="cc_id(var)",
        doc="Alias of component_id.", alias_of="component_id",
    ),
    "component_size": BuiltinFunction(
        "component_size", _make_cc_size(_CC4, "component_size"), signature="component_size(var)",
        doc="L4: per-cell size of the 4-connected equal-value component (O(N²)).",
    ),
    "cc_size": BuiltinFunction(
        "cc_size", _make_cc_size(_CC4, "cc_size"), signature="cc_size(var)",
        doc="Alias of component_size.", alias_of="component_size",
    ),
    "component_count": BuiltinFunction(
        "component_count", _make_cc_count(_CC4, "component_count"),
        signature="component_count(var, value)",
        doc="L2: number of 4-connected components whose cells hold that value.",
    ),
    "cc_count": BuiltinFunction(
        "cc_count", _make_cc_count(_CC4, "cc_count"), signature="cc_count(var, value)",
        doc="Alias of component_count.", alias_of="component_count",
    ),
    "same_component": BuiltinFunction(
        "same_component", _fn_same_component, signature="same_component(var, p, q)",
        doc="L3: whether two cells share a 4-connected equal-value component (uses canonical ids).",
    ),
    "cc_root": BuiltinFunction(
        "cc_root", _make_cc_root(_CC4, "cc_root"), signature="cc_root(var, cell)",
        doc="Whether the cell is the representative of its component.",
    ),
    "cc_count_in": BuiltinFunction(
        "cc_count_in", _make_cc_count_in(_CC4, "cc_count_in"),
        signature="cc_count_in(var, value, region)",
        doc="Number of 4-CC of `value` when cells outside the region are walls.",
    ),
    "cc_size_in": BuiltinFunction(
        "cc_size_in", _make_cc_size_in(_CC4, "cc_size_in"),
        signature="cc_size_in(var, cell, region)",
        doc="Size of cell's 4-CC under region-masked connectivity (0 if cell not in region).",
    ),
    "cc_width": BuiltinFunction(
        "cc_width", _make_cc_width(_CC4, "cc_width"), signature="cc_width(var)",
        doc="Per-cell bounding-box width of the same-value 4-CC (O(N²)).",
    ),
    "cc_height": BuiltinFunction(
        "cc_height", _make_cc_height(_CC4, "cc_height"), signature="cc_height(var)",
        doc="Per-cell bounding-box height of the same-value 4-CC (O(N²)).",
    ),
    "cc_is_rect": BuiltinFunction(
        "cc_is_rect", _fn_cc_is_rect, signature="cc_is_rect(var, cell)",
        doc="True iff the cell's 4-CC fills its bounding box (size == width * height).",
    ),
    "cc_corner_count": BuiltinFunction(
        "cc_corner_count", _fn_cc_corner_count, signature="cc_corner_count(var, cell)",
        doc="How many of the region's four bbox corners are occupied (P4B).",
    ),
    "cc_notch_count": BuiltinFunction(
        "cc_notch_count", _fn_cc_notch_count, signature="cc_notch_count(var, cell)",
        doc="Number of 2x2 windows containing exactly three cells of this region.",
    ),
    "cc_full2x2": BuiltinFunction(
        "cc_full2x2", _fn_cc_full2x2, signature="cc_full2x2(var, cell)",
        doc="Number of 2x2 windows filled by this region.",
    ),
    "cc_deg_count": BuiltinFunction(
        "cc_deg_count", _fn_cc_deg_count, signature="cc_deg_count(var, cell, d)",
        doc="How many cells of this region have orthogonal degree d (0..4).",
    ),
    "cc_half_count": BuiltinFunction(
        "cc_half_count", _fn_cc_half_count, signature="cc_half_count(var, cell, axis, side)",
        doc="Cells of this region strictly above/below (axis=0) or left/right (axis=1); side 0=neg, 1=pos.",
    ),
    "cc_line_count": BuiltinFunction(
        "cc_line_count", _fn_cc_line_count, signature="cc_line_count(var, cell, axis)",
        doc="Same-region cells on this row (axis=0) or column (axis=1). Not bbox width/height.",
    ),
    "cc8_id": BuiltinFunction(
        "cc8_id", _make_cc_id(_CC8, "cc8_id"), signature="cc8_id(var)",
        doc="Per-cell id of the 8-connected component of equal-valued cells.",
    ),
    "cc8_size": BuiltinFunction(
        "cc8_size", _make_cc_size(_CC8, "cc8_size"), signature="cc8_size(var)",
        doc="Per-cell size of the 8-connected component.",
    ),
    "cc8_count": BuiltinFunction(
        "cc8_count", _make_cc_count(_CC8, "cc8_count"), signature="cc8_count(var, value)",
        doc="Number of 8-connected components holding that value.",
    ),
    "cc8_root": BuiltinFunction(
        "cc8_root", _make_cc_root(_CC8, "cc8_root"), signature="cc8_root(var, cell)",
        doc="Whether the cell represents its 8-connected component.",
    ),
    "cc8_count_in": BuiltinFunction(
        "cc8_count_in", _make_cc_count_in(_CC8, "cc8_count_in"),
        signature="cc8_count_in(var, value, region)",
        doc="Number of 8-CC of `value` when cells outside the region are walls.",
    ),
    "cc8_size_in": BuiltinFunction(
        "cc8_size_in", _make_cc_size_in(_CC8, "cc8_size_in"),
        signature="cc8_size_in(var, cell, region)",
        doc="Size of cell's 8-CC under region-masked connectivity (0 if cell not in region).",
    ),
    "drop_covers": BuiltinFunction(
        "drop_covers", _fn_drop_covers, signature="drop_covers(var, start_row)",
        doc="Black 4-components fall rigidly down and occupy exactly rows start_row..end.",
    ),
    # -- loops ----------------------------------------------------------
    "deg": BuiltinFunction(
        "deg", _fn_deg, signature="deg(var, corner)",
        doc="Number of selected lattice edges meeting a corner.",
    ),
    "cdeg": BuiltinFunction(
        "cdeg", _fn_cdeg, signature="cdeg(var, cell)",
        doc="Number of selected cell-to-cell links leaving a cell.",
    ),
    "loop": BuiltinFunction(
        "loop", _fn_loop, signature="loop(var)",
        doc="Edge variable forms exactly one closed loop on the corner lattice.",
    ),
    "cloop": BuiltinFunction(
        "cloop", _fn_cloop, signature="cloop(var)",
        doc="Edge variable forms exactly one closed loop through cell centres.",
    ),
    "connect_edges": BuiltinFunction(
        "connect_edges", _fn_connect_edges, signature="connect_edges(var)",
        doc="Selected corner-lattice edges form a single connected component.",
    ),
    "connect_links": BuiltinFunction(
        "connect_links", _fn_connect_links, signature="connect_links(var)",
        doc="Selected cell-to-cell links form a single connected component.",
    ),
}

ELEMENTWISE_BUILTINS: dict[str, BuiltinFunction] = {
    "abs": BuiltinFunction(
        "abs", _fn_abs, elementwise=True, signature="abs(x)",
        doc="Absolute value, applied element-wise over lists.",
    ),
    "b2i": BuiltinFunction(
        "b2i", _fn_b2i, elementwise=True, signature="b2i(x)",
        doc="Boolean to 0/1 integer, applied element-wise.",
    ),
}

DEBUG_BUILTINS: dict[str, BuiltinFunction] = {
    "print": BuiltinFunction(
        "print", _fn_print, signature="print(expr, ...)",
        doc="Debug: print the variable/region/list of each argument at compile time.",
    ),
}

META_BUILTINS: dict[str, BuiltinFunction] = {
    "solve": BuiltinFunction(
        "solve", lambda ctx, args, pos: ctx.meta_solve(args, pos),
        signature="solve([timeout_ms])",
        doc="Meta: solve the constraints generated so far. Returns a snapshot with .sat / .status / .<var>.",
    ),
    "exclude": BuiltinFunction(
        "exclude", lambda ctx, args, pos: ctx.meta_exclude(args, pos),
        signature="exclude(s [, vars...])",
        doc="Meta: constraint that the decisive variables differ from snapshot s.",
    ),
    "unique_over": BuiltinFunction(
        "unique_over", lambda ctx, args, pos: ctx.meta_unique_over(args, pos),
        signature="unique_over(v1, v2, ...)",
        doc="Meta: restrict uniqueness / exclude() to these decisive variables.",
    ),
    "require": BuiltinFunction(
        "require", lambda ctx, args, pos: ctx.meta_require(args, pos),
        signature="require(cond, msg)",
        doc="Meta: compile-time assertion. cond must be a Python bool.",
    ),
    "fail": BuiltinFunction(
        "fail", lambda ctx, args, pos: ctx.meta_fail(args, pos),
        signature="fail(msg)",
        doc="Meta: abort compilation with a message.",
    ),
    "domain_of": BuiltinFunction(
        "domain_of", lambda ctx, args, pos: ctx.meta_domain_of(args, pos),
        signature="domain_of(var)",
        doc="Compile-time list of integers in var.domain (inclusive).",
    ),
    "emit_witness": BuiltinFunction(
        "emit_witness", lambda ctx, args, pos: ctx.meta_emit_witness(args, pos),
        signature="emit_witness(tag, value)",
        doc="Meta: record a (tag, int) witness on the solve result.",
    ),
    "solve_count": BuiltinFunction(
        "solve_count", lambda ctx, args, pos: ctx.meta_solve_count(args, pos),
        signature="solve_count()",
        doc="Meta: how many solve() calls have run in this meta: block.",
    ),
}

BUILTIN_FUNCTIONS: dict[str, BuiltinFunction] = {
    **AGGREGATE_BUILTINS,
    **ELEMENTWISE_BUILTINS,
    **DEBUG_BUILTINS,
    **META_BUILTINS,
}


# Direction constants exposed to programs (and documented in the function table).
DIRECTION_CONSTANTS: dict[str, int] = {
    "UP": 0,
    "DOWN": 1,
    "LEFT": 2,
    "RIGHT": 3,
    "UP_LEFT": 4,
    "UP_RIGHT": 5,
    "DOWN_LEFT": 6,
    "DOWN_RIGHT": 7,
}


def make_constants(grid) -> dict[str, Any]:
    """Build the constant environment (``rows`` / ``cols`` + directions)."""

    rows = [RegionValue.of(PointKind.CELL, [(r, c) for c in range(grid.cols)]) for r in range(grid.rows)]
    cols = [RegionValue.of(PointKind.CELL, [(r, c) for r in range(grid.rows)]) for c in range(grid.cols)]
    env: dict[str, Any] = {"rows": rows, "cols": cols}
    env.update(DIRECTION_CONSTANTS)
    env["dirs4"] = [0, 1, 2, 3]
    env["dirs8"] = [0, 1, 2, 3, 4, 5, 6, 7]
    return env


# -- documentation table for the UI viewer ------------------------------------


@dataclass(frozen=True)
class DocEntry:
    name: str
    signature: str
    doc: str
    category: str


def function_table() -> list[DocEntry]:
    """A browsable table of builtins, constants and operators for the UI."""

    entries: list[DocEntry] = []
    for fn in BUILTIN_FUNCTIONS.values():
        if fn.name in DEBUG_BUILTINS:
            category = "Debug"
        elif fn.name in META_BUILTINS:
            category = "Meta"
        elif fn.alias_of:
            category = "Alias"
        elif fn.elementwise:
            category = "Element-wise"
        else:
            category = "Function"
        entries.append(DocEntry(fn.name, fn.signature or f"{fn.name}(...)", fn.doc, category))

    constants = [
        ("rows", "rows", "List of all row regions."),
        ("cols", "cols", "List of all column regions."),
        ("UP", "UP = 0", "Direction up (for dir())."),
        ("DOWN", "DOWN = 1", "Direction down."),
        ("LEFT", "LEFT = 2", "Direction left."),
        ("RIGHT", "RIGHT = 3", "Direction right."),
        ("UP_LEFT", "UP_LEFT = 4", "Diagonal up-left."),
        ("UP_RIGHT", "UP_RIGHT = 5", "Diagonal up-right."),
        ("DOWN_LEFT", "DOWN_LEFT = 6", "Diagonal down-left."),
        ("DOWN_RIGHT", "DOWN_RIGHT = 7", "Diagonal down-right."),
        ("dirs4", "dirs4", "The four orthogonal directions [UP, DOWN, LEFT, RIGHT]."),
        ("dirs8", "dirs8", "The eight directions including diagonals."),
    ]
    for name, sig, doc in constants:
        entries.append(DocEntry(name, sig, doc, "Constant"))

    operators = [
        ("and / &&", "a and b", "Logical and; on two lists/regions, merges them instead."),
        ("or / ||", "a or b", "Logical or."),
        ("xor / ^", "a ^ b", "Logical exclusive-or."),
        ("not / !", "not a", "Logical negation."),
        ("=>", "a => b", "Implies (lowest precedence, right-associative)."),
        ("== != < <= > >=", "a == b", "Comparisons (broadcast element-wise)."),
        ("+ - * / %", "a + b", "Arithmetic (integer division/modulo when concrete)."),
        ("fn / ->", "fn (p) -> expr", "Anonymous function. Captures enclosing bindings (unlike def)."),
        ("x[region]", "x[row(0)]", "Index a variable by a region/integer."),
    ]
    for name, sig, doc in operators:
        entries.append(DocEntry(name, sig, doc, "Operator"))

    cc_members = [
        ("cc", "c[cell(0,0)]",
         "A region (cc) variable: its value at each cell is that cell's region "
         "id (built-in 4-connectivity). Used bare it is the per-cell ids."),
        ("c.id", "c.id[cell(0,0)]",
         "Per-cell region id; equal id ⟹ connected, id = region's min r*cols+c."),
        ("c.size", "c.size[cell(0,0)]",
         "Per-cell region size (count of cells sharing its id); O(N²), use with care."),
        ("c.border", "c.border[edge_of(cell(0,0))]",
         "Per-edge 0/1: 1 iff the edge is on the grid boundary or separates two "
         "different regions."),
        ("c.bbox_w / c.bbox_h", "c.bbox_w[cell(0,0)]",
         "Per-cell bounding-box width/height of the region (O(N²))."),
        ("c.deg", "c.deg[cell(0,0)]",
         "Orthogonal neighbours that share this cell's region id."),
    ]
    for name, sig, doc in cc_members:
        entries.append(DocEntry(name, sig, doc, "Region (cc)"))

    return entries
