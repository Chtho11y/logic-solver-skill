"""Runtime value model and broadcasting for the puzzle DSL compiler.

Values flowing through the compiler are one of:

* a *scalar* -- a Python ``int``/``bool`` or a z3 expression;
* a *list* -- a (possibly nested) Python ``list`` of values;
* a :class:`RegionValue` -- an ordered set of grid points (used as an index or
  iterated over);
* a :class:`VarValue` -- a variable's full set of z3 quantities (one per point
  of its kind); used directly it behaves like the list of all its quantities.

Broadcasting follows the spec: a list combines with a scalar element-wise, and
two lists combine when their lengths match or one of them is 1 (applied
recursively for nested lists).

UI-independent (no PyQt import; broadcasting takes a plain callable so this
module needs no z3 dependency).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..models import Point, PointKind


def point_sort_key(point: Point) -> tuple:
    """Deterministic ordering for points (cells/corners before edges)."""

    if len(point) == 2:
        return (0, "", int(point[0]), int(point[1]))
    return (1, str(point[0]), int(point[1]), int(point[2]))


def sort_points(points) -> tuple[Point, ...]:
    return tuple(sorted(points, key=point_sort_key))


@dataclass(frozen=True)
class RegionValue:
    """An ordered collection of points of a single kind."""

    kind: PointKind
    points: tuple[Point, ...]

    @classmethod
    def of(cls, kind: PointKind, points) -> "RegionValue":
        return cls(kind=kind, points=sort_points(points))


@dataclass
class VarValue:
    """A variable's full set of z3 quantities, keyed by point."""

    name: str
    kind: PointKind
    quantities: dict[Point, Any]
    order: tuple[Point, ...]
    bool_backed: bool = False

    def as_list(self) -> list:
        return [self.quantities[p] for p in self.order]


def _as_python_int(value: Any) -> int | None:
    # Python bool is a subclass of int; do not treat True/False as 1/0 here.
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def is_bool_atom(value: Any, z3) -> bool:
    """True for Python bools and z3 Bool *variables* (not comparison formulas)."""

    if isinstance(value, bool):
        return True
    return bool(z3.is_expr(value) and z3.is_bool(value) and z3.is_const(value))


def is_bool_expr(value: Any, z3) -> bool:
    if isinstance(value, bool):
        return True
    return bool(z3.is_expr(value) and z3.is_bool(value))


def as_int(q: Any, z3) -> Any:
    """Lift a boolean *variable* to ``0/1``; integers and formulas pass through."""

    if isinstance(q, bool):
        return 1 if q else 0
    if isinstance(q, int):
        return q
    if is_bool_atom(q, z3):
        return z3.If(q, 1, 0)
    return q


def _as_z3_bool(q: Any, z3) -> Any:
    if isinstance(q, bool):
        return z3.BoolVal(q)
    if is_bool_expr(q, z3):
        return q
    return as_bool(q, 1, z3)


def as_bool(q: Any, v: Any, z3) -> Any:
    """Whether quantity ``q`` equals integer ``v`` (boolean-aware)."""

    if isinstance(v, bool) or is_bool_expr(v, z3):
        return _as_z3_bool(q, z3) == _as_z3_bool(v, z3)
    target = _as_python_int(v)
    if target is None:
        return q == v
    if isinstance(q, bool):
        return q is (target == 1) if target in (0, 1) else False
    if isinstance(q, int):
        return q == target
    if is_bool_atom(q, z3):
        if target == 1:
            return q
        if target == 0:
            return z3.Not(q)
        return z3.BoolVal(False)
    return q == target


def as_ne(q: Any, v: Any, z3) -> Any:
    """Whether quantity ``q`` differs from integer ``v`` (boolean-aware)."""

    if isinstance(q, bool) or isinstance(v, bool) or is_bool_atom(q, z3) or is_bool_atom(v, z3):
        return z3.Not(as_same(q, v, z3))
    target = _as_python_int(v)
    if target is None:
        return q != v
    return q != target


def as_same(a: Any, b: Any, z3) -> Any:
    """Whether two quantities are equal, mixing Bool and Int safely."""

    if isinstance(a, bool) and isinstance(b, bool):
        return a is b
    if is_bool_expr(a, z3) or is_bool_expr(b, z3) or isinstance(a, bool) or isinstance(b, bool):
        return _as_z3_bool(a, z3) == _as_z3_bool(b, z3)
    av = _as_python_int(a)
    bv = _as_python_int(b)
    if av is not None and bv is not None:
        return av == bv
    if av is not None:
        return as_bool(b, av, z3)
    if bv is not None:
        return as_bool(a, bv, z3)
    return a == b


class BroadcastError(ValueError):
    """Raised when two shapes cannot be broadcast together."""


def to_numeric(value: Any) -> Any:
    """Coerce a value into something usable in arithmetic/logic.

    ``VarValue`` becomes the list of its quantities; lists are mapped
    recursively; scalars pass through. ``RegionValue`` is rejected.
    """

    if isinstance(value, VarValue):
        items = value.as_list()
        if value.bool_backed:
            import z3

            return [as_int(q, z3) for q in items]
        return items
    if isinstance(value, RegionValue):
        raise BroadcastError("a region cannot be used as a number")
    if isinstance(value, list):
        return [to_numeric(item) for item in value]
    return value


def broadcast(a: Any, b: Any, fn: Callable[[Any, Any], Any]) -> Any:
    """Combine ``a`` and ``b`` with ``fn`` following broadcasting rules."""

    a = to_numeric(a)
    b = to_numeric(b)
    a_list = isinstance(a, list)
    b_list = isinstance(b, list)
    if not a_list and not b_list:
        return fn(a, b)
    if a_list and not b_list:
        return [broadcast(x, b, fn) for x in a]
    if b_list and not a_list:
        return [broadcast(a, y, fn) for y in b]
    if len(a) == len(b):
        return [broadcast(x, y, fn) for x, y in zip(a, b)]
    if len(a) == 1:
        return [broadcast(a[0], y, fn) for y in b]
    if len(b) == 1:
        return [broadcast(x, b[0], fn) for x in a]
    raise BroadcastError(f"cannot broadcast lists of length {len(a)} and {len(b)}")


def map_elementwise(value: Any, fn: Callable[[Any], Any]) -> Any:
    """Apply a single-element ``fn`` to a value, recursing into lists."""

    value = to_numeric(value)
    if isinstance(value, list):
        return [map_elementwise(item, fn) for item in value]
    return fn(value)


def flatten_scalars(value: Any) -> list:
    """Flatten a value into a flat list of scalar quantities."""

    value = to_numeric(value)
    if isinstance(value, list):
        out: list = []
        for item in value:
            out.extend(flatten_scalars(item))
        return out
    return [value]
