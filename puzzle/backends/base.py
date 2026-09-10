"""Backend-neutral contracts used by the puzzle DSL compiler."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


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

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "available": self.available,
            "reason": self.reason,
            "supportsTimeout": self.supports_timeout,
            "supportsGraphPrimitives": self.supports_graph_primitives,
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
