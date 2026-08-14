"""Core data model shared by the puzzle DSL, the solver runner and the server.

A board is an ``rows x cols`` grid of *cells*; the lattice around them gives
*corners* and *edges*:

* ``cell``   -- ``(r, c)`` with ``0 <= r < rows``, ``0 <= c < cols``
* ``corner`` -- ``(r, c)`` with ``0 <= r <= rows``, ``0 <= c <= cols``
* ``edge``   -- ``(orient, r, c)`` where ``orient`` is ``"H"`` (the horizontal
  edge above cell ``(r, c)``) or ``"V"`` (the vertical edge left of cell
  ``(r, c)``)

UI-independent (no PyQt / no z3 import).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Tuple, Union

# A cell/corner is (r, c); an edge is (orient, r, c).
Point = Union[Tuple[int, int], Tuple[str, int, int]]


class PointKind(Enum):
    """Which lattice a variable / region lives on."""

    CELL = "cell"
    CORNER = "corner"
    EDGE = "edge"

    @property
    def label(self) -> str:
        return self.value

    @classmethod
    def parse(cls, text: str) -> "PointKind":
        key = str(text).strip().lower()
        for kind in cls:
            if kind.value == key:
                return kind
        raise ValueError(f"unknown point kind {text!r} (use cell/corner/edge)")


class VarType(Enum):
    """How a variable is solved and echoed back."""

    NORMAL = "normal"
    CC = "cc"
    CONSTANT = "constant"

    @classmethod
    def parse(cls, text: str) -> "VarType":
        key = str(text).strip().lower()
        for vtype in cls:
            if vtype.value == key:
                return vtype
        raise ValueError(f"unknown variable type {text!r} (use normal/cc/constant)")


# P1 step 1: adapters land with this False (Int encoding unchanged).
# P1 step 2 flips it so domain-(0,1) NORMAL vars become z3.Bool.
ENABLE_BOOLEAN_VARS = True


@dataclass
class Variable:
    """One solvable (or constant) quantity per point of ``kind``."""

    name: str
    kind: PointKind = PointKind.CELL
    var_type: VarType = VarType.NORMAL
    domain: tuple[int, int] | None = None
    givens: dict[Point, int] = field(default_factory=dict)

    def with_givens(self, givens: dict[Point, int]) -> "Variable":
        return Variable(self.name, self.kind, self.var_type, self.domain, dict(givens))

    @property
    def is_boolean(self) -> bool:
        """Whether this variable can be stored as ``z3.Bool``.

        P1 step 1 keeps the flag off so the adapter layer can land with a
        byte-identical baseline. Flip :data:`ENABLE_BOOLEAN_VARS` to enable.
        """

        if not ENABLE_BOOLEAN_VARS:
            return False
        return self.var_type is VarType.NORMAL and self.domain == (0, 1)


@dataclass(frozen=True)
class Region:
    """A named, ordered set of points of a single kind."""

    name: str
    kind: PointKind
    points: tuple[Point, ...]


def parse_point(text: Any, kind: PointKind) -> Point:
    """Parse a JSON point key/list into a :data:`Point`.

    Accepts ``"r,c"`` / ``[r, c]`` for cells & corners and ``"H,r,c"`` /
    ``["H", r, c]`` for edges.
    """

    if isinstance(text, (list, tuple)):
        parts = [str(p) for p in text]
    else:
        parts = [p.strip() for p in str(text).split(",")]
    if kind is PointKind.EDGE:
        if len(parts) != 3:
            raise ValueError(f"edge point must be 'H,r,c' or 'V,r,c', got {text!r}")
        orient = parts[0].strip().upper()
        if orient not in ("H", "V"):
            raise ValueError(f"edge orientation must be H or V, got {parts[0]!r}")
        return (orient, int(parts[1]), int(parts[2]))
    if len(parts) != 2:
        raise ValueError(f"{kind.label} point must be 'r,c', got {text!r}")
    return (int(parts[0]), int(parts[1]))


def point_key(point: Point) -> str:
    """Serialise a point back to its JSON key form."""

    return ",".join(str(part) for part in point)
