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
from .values import RegionValue, VarValue, flatten_scalars, sort_points, to_numeric


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
    items = _flatten_args(args)
    if not items:
        return 0
    return ctx.z3.Sum(items)


def _fn_distinct(ctx, args, pos):
    items = _flatten_args(args)
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
    return RegionValue.of(PointKind.CELL, points)


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
    return ctx.z3.Sum([ctx.z3.If(item == value, 1, 0) for item in items])


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


def _build_value_cc(ctx, var: VarValue, deltas) -> dict:
    """Encode maximal same-valued connected components of a cell variable.

    Produces per-cell ``id`` (the minimum linear index of the component) plus a
    spanning-tree ``dist`` witness so that *equal id* is equivalent to
    *connected through cells of the same value*.
    """

    z3 = ctx.z3
    grid = ctx.grid
    cols = grid.cols
    cells = sort_points(var.order)
    cell_set = set(cells)
    tag = f"{var.name}#cc{len(deltas)}"
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
            z3.And(var.quantities[n] == xp, ids[n] == idp, dist[n] == dp - 1)
            for n in neighbours
        ]
        ctx.add_aux(z3.Implies(dp > 0, z3.Or(parents) if parents else z3.BoolVal(False)))
        for n in neighbours:
            ctx.add_aux(z3.Implies(var.quantities[n] == xp, ids[n] == idp))
    return {"id": ids, "dist": dist, "cells": cells}


def _value_cc(ctx, var: VarValue, deltas):
    return ctx.memo(("valuecc", var.name, len(deltas)), lambda: _build_value_cc(ctx, var, deltas))


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


def _ensure_cc_size(ctx, var: VarValue, deltas) -> dict:
    cc = _value_cc(ctx, var, deltas)
    if "size" in cc:
        return cc
    z3 = ctx.z3
    cells = cc["cells"]
    ids = cc["id"]
    sizes = {p: z3.Int(f"{var.name}#cc{len(deltas)}#n#r{p[0]}c{p[1]}") for p in cells}
    for p in cells:
        ctx.add_aux(sizes[p] == z3.Sum([z3.If(ids[q] == ids[p], 1, 0) for q in cells]))
    cc["size"] = sizes
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
        value = to_numeric(args[1])
        cc = _value_cc(ctx, var, deltas)
        z3 = ctx.z3
        cols = ctx.grid.cols
        terms = [
            z3.If(z3.And(cc["id"][p] == p[0] * cols + p[1], var.quantities[p] == value), 1, 0)
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
        parts.append(z3.Implies(var.quantities[p] != 1, drop[p] == 0))
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
                both = z3.And(var.quantities[p] == 1, var.quantities[q] == 1)
                parts.append(z3.Implies(both, p[0] + drop[p] < q[0] + drop[q]))
        for dest_r in range(rows):
            hits = [
                z3.If(z3.And(var.quantities[p] == 1, p[0] + drop[p] == dest_r), 1, 0)
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


def _fn_runs(ctx, args, pos):
    """The 0/1 sequence's maximal runs of 1 have exactly the given lengths.

    ``lengths`` is an ordered list of concrete integers (typically read from
    ``param(...)``); a single ``0`` means "no filled cell at all".
    """

    if len(args) != 2:
        raise CompileError("runs(list, lengths) takes two arguments", pos.line, pos.col)
    z3 = ctx.z3
    seq = flatten_scalars(args[0])
    raw = to_numeric(args[1])
    if not isinstance(raw, list):
        raw = [raw]
    lengths = [_as_int(item, "runs") for item in raw]
    lengths = [n for n in lengths if n > 0]
    n = len(seq)
    if not lengths:
        return z3.And([item == 0 for item in seq]) if seq else z3.BoolVal(True)
    if sum(lengths) + len(lengths) - 1 > n:
        return z3.BoolVal(False)
    starts = [ctx.new_int("runs#s") for _ in lengths]
    parts = [starts[0] >= 0]
    for i in range(1, len(lengths)):
        parts.append(starts[i] >= starts[i - 1] + lengths[i - 1] + 1)
    parts.append(starts[-1] + lengths[-1] <= n)
    for j, item in enumerate(seq):
        covered = [
            z3.And(starts[i] <= j, j < starts[i] + lengths[i]) for i in range(len(lengths))
        ]
        parts.append((item == 1) == z3.Or(covered))
    return z3.And(parts)


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
    return ctx.z3.Sum([var.quantities[e] for _, e in graph[point]])


def _fn_cdeg(ctx, args, pos):
    if len(args) != 2:
        raise CompileError("cdeg(var, cell) takes two arguments", pos.line, pos.col)
    var = _expect_edge_var(args[0], "cdeg", pos)
    cell = _expect_cell(args[1], "cdeg", pos)
    graph, _ = ctx.memo(("cellgraph",), lambda: _cell_graph(ctx.grid))
    return ctx.z3.Sum([var.quantities[e] for _, e in graph[cell]])


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
        incident = [var.quantities[e] for _, e in graph[node]]
        used[node] = z3.Sum(incident) > 0 if incident else z3.BoolVal(False)
    for node in nodes:
        lin = index[node]
        idn, dn = ids[node], dist[node]
        ctx.add_aux(z3.And(idn >= 0, idn <= lin))
        ctx.add_aux(dn >= 0)
        ctx.add_aux((dn == 0) == (idn == lin))
        parents = [
            z3.And(var.quantities[e] == 1, ids[nb] == idn, dist[nb] == dn - 1)
            for nb, e in graph[node]
        ]
        ctx.add_aux(z3.Implies(dn > 0, z3.Or(parents) if parents else z3.BoolVal(False)))
        for nb, e in graph[node]:
            ctx.add_aux(z3.Implies(var.quantities[e] == 1, ids[nb] == idn))
    roots = z3.Sum([z3.If(z3.And(used[n], dist[n] == 0), 1, 0) for n in nodes])
    return roots, used


def _loop_common(ctx, var, graph, tag, degrees, single):
    z3 = ctx.z3
    key = (tag, var.name)
    roots, _used = ctx.memo(key, lambda: _link_connect(ctx, var, graph, ctx.grid.cols, tag))
    parts = []
    for node, links in graph.items():
        total = z3.Sum([var.quantities[e] for _, e in links]) if links else 0
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
        ctx.add_aux(var.quantities[edge] == 0)
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
        ctx.add_aux(var.quantities[edge] == 0)
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
    "runs": BuiltinFunction(
        "runs", _fn_runs, signature="runs(list, lengths)",
        doc="The 0/1 sequence's maximal runs of 1 match the ordered lengths.",
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
    # -- connectivity of equal-valued cells -----------------------------
    "cc_id": BuiltinFunction(
        "cc_id", _make_cc_id(_CC4, "cc_id"), signature="cc_id(var)",
        doc="Per-cell id of the 4-connected component of equal-valued cells.",
    ),
    "cc_size": BuiltinFunction(
        "cc_size", _make_cc_size(_CC4, "cc_size"), signature="cc_size(var)",
        doc="Per-cell size of that component (O(N²), use sparingly).",
    ),
    "cc_count": BuiltinFunction(
        "cc_count", _make_cc_count(_CC4, "cc_count"), signature="cc_count(var, value)",
        doc="Number of 4-connected components whose cells hold that value.",
    ),
    "cc_root": BuiltinFunction(
        "cc_root", _make_cc_root(_CC4, "cc_root"), signature="cc_root(var, cell)",
        doc="Whether the cell is the representative of its component.",
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

BUILTIN_FUNCTIONS: dict[str, BuiltinFunction] = {
    **AGGREGATE_BUILTINS,
    **ELEMENTWISE_BUILTINS,
    **DEBUG_BUILTINS,
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
    ]
    for name, sig, doc in cc_members:
        entries.append(DocEntry(name, sig, doc, "Region (cc)"))

    return entries
