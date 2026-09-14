"""Backend-neutral contracts used by the puzzle DSL compiler."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence, runtime_checkable


class BackendError(RuntimeError):
    """Base class for solver backend failures."""


class BackendUnavailableError(BackendError):
    """Raised when a requested concrete solver is not installed."""


class BackendTimeoutError(BackendError):
    """Raised when a concrete solver reaches its configured time limit."""


class BackendUnknownError(BackendError):
    """Raised when a concrete solver cannot decide satisfiability."""


@dataclass(frozen=True)
class BackendInfo:
    """Runtime availability and capabilities of one cspuz solver backend."""

    name: str
    label: str
    available: bool
    reason: str = ""
    supports_timeout: bool = False
    supports_graph_primitives: bool = False
    features: tuple[str, ...] = field(default_factory=tuple)

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "available": self.available,
            "reason": self.reason,
            "supportsTimeout": self.supports_timeout,
            "supportsGraphPrimitives": self.supports_graph_primitives,
            "features": list(self.features),
        }


@runtime_checkable
class ConstraintModel(Protocol):
    """Small expression API consumed by ``puzzle.dsl``.

    The protocol prevents concrete solver objects from leaking into the DSL
    layer and keeps future model implementations replaceable.
    """

    def Int(
        self, name: str, lo: int | None = None, hi: int | None = None
    ) -> Any: ...

    def BoolVal(self, value: bool) -> Any: ...

    def Sum(self, values: Any) -> Any: ...

    def Distinct(self, values: Any) -> Any: ...

    def And(self, *values: Any) -> Any: ...

    def Or(self, *values: Any) -> Any: ...

    def Not(self, value: Any) -> Any: ...

    def Xor(self, left: Any, right: Any) -> Any: ...

    def Implies(self, left: Any, right: Any) -> Any: ...

    def If(self, condition: Any, when_true: Any, when_false: Any) -> Any: ...

    def is_expr(self, value: Any) -> bool: ...

    def is_bool(self, value: Any) -> bool: ...

    def bounds(self, value: Any) -> tuple[int, int] | None: ...

    def add_constraints(self, constraints: Any) -> None: ...

    def find_answer(self, backend: str, timeout_ms: int | None = None) -> bool: ...

    def value(self, variable: Any) -> int | bool | None: ...

    def vertices_connected(
        self,
        is_active: Sequence[Any],
        edges: Sequence[tuple[int, int]],
    ) -> Any:
        """Bool: the active vertices form at most one connected component."""
        ...

    def edges_single_cycle(
        self,
        is_active: Sequence[Any],
        pairs: Sequence[tuple[int, int]],
        n_vertices: int,
        *,
        nonempty: bool = True,
    ) -> Any:
        """Bool: selected edges form one cycle (empty allowed iff not nonempty)."""
        ...

    def edges_connected(
        self,
        is_active: Sequence[Any],
        pairs: Sequence[tuple[int, int]],
        n_vertices: int,
        *,
        nonempty: bool = True,
    ) -> Any:
        """Bool: selected edges form one connected component."""
        ...

    def vertices_isolated_and_complement_connected(
        self,
        is_active: Sequence[Any],
        pairs: Sequence[tuple[int, int]],
        shape: tuple[int, int] | None = None,
    ) -> Any:
        """Bool: active vertices are not adjacent and do not split the rest."""
        ...

    def graph_division(
        self,
        group_size: Sequence[Any],
        edges: Sequence[tuple[int, int]],
        is_border: Sequence[Any],
    ) -> Any:
        """Bool: vertices are partitioned by ``is_border`` into connected groups.

        ``group_size[i]`` is the number of vertices in the group that contains
        vertex ``i``. ``is_border[e]`` is true iff edge ``e`` joins two
        different groups. Must be posted as a top-level CSP statement.
        """
        ...
