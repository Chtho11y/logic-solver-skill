"""Runtime value model and broadcasting for the puzzle DSL compiler.

Values flowing through the compiler are one of:

* a *scalar* -- a Python ``int``/``bool`` or a solver expression;
* a *list* -- a (possibly nested) Python ``list`` of values;
* a :class:`RegionValue` -- an ordered set of grid points (used as an index or
  iterated over);
* a :class:`VarValue` -- a variable's full set of solver terms (one per point
  of its kind); used directly it behaves like the list of all its quantities.

Broadcasting follows the spec: a list combines with a scalar element-wise, and
two lists combine when their lengths match or one of them is 1 (applied
recursively for nested lists).

UI-independent (no PyQt import or concrete solver dependency).
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
    """A variable's full set of solver quantities, keyed by point."""

    name: str
    kind: PointKind
    quantities: dict[Point, Any]
    order: tuple[Point, ...]

    def as_list(self) -> list:
        return [self.quantities[p] for p in self.order]


class BroadcastError(ValueError):
    """Raised when two shapes cannot be broadcast together."""


def to_numeric(value: Any) -> Any:
    """Coerce a value into something usable in arithmetic/logic.

    ``VarValue`` becomes the list of its quantities; lists are mapped
    recursively; scalars pass through. ``RegionValue`` is rejected.
    """

    if isinstance(value, VarValue):
        return value.as_list()
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
