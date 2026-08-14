"""Solver session protocol used by meta-solve (``meta:`` / ``scope:`` / ``solve()``).

The compiler never imports :mod:`puzzle.dsl.solver`. ``solver.py`` injects a
:class:`Z3Session` when ``run_meta=True``; otherwise the compiler never
touches a z3 Solver and existing programs compile as before.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from ..models import Point, PointKind, VarType


class SolverSession(Protocol):
    def add(self, constraint) -> None: ...
    def push(self) -> None: ...
    def pop(self) -> None: ...
    def check(self, timeout_ms: int | None = None) -> str: ...
    def value_of(self, term) -> int: ...
    def is_determined(self, term) -> bool: ...


@dataclass
class SolutionValue:
    """Compile-time snapshot of one ``solve()`` call.

    ``.<varname>`` is a CONSTANT-like :class:`VarValue` of Python ints so
    ``at(s.x, p)`` constant-folds. ``.sat`` / ``.status`` are compile-time
    scalars.
    """

    status: str
    values: dict[str, dict[Point, int]] = field(default_factory=dict)
    kinds: dict[str, PointKind] = field(default_factory=dict)

    @property
    def sat(self) -> bool:
        return self.status == "sat"


class Z3Session:
    """z3-backed :class:`SolverSession` with a fixed random seed."""

    def __init__(self, z3, timeout_ms: int | None = None, seed: int = 1) -> None:
        self._z3 = z3
        self._solver = z3.Solver()
        self._solver.set("random_seed", int(seed))
        self._timeout_ms = timeout_ms
        self._model = None
        self._status = "unknown"

    def add(self, constraint) -> None:
        self._solver.add(constraint)

    def push(self) -> None:
        self._solver.push()

    def pop(self) -> None:
        self._solver.pop()

    def check(self, timeout_ms: int | None = None) -> str:
        ms = self._timeout_ms if timeout_ms is None else timeout_ms
        if ms:
            self._solver.set("timeout", int(ms))
        result = self._solver.check()
        z3 = self._z3
        if result == z3.sat:
            self._model = self._solver.model()
            self._status = "sat"
        elif result == z3.unsat:
            self._model = None
            self._status = "unsat"
        else:
            self._model = None
            self._status = "unknown"
        return self._status

    def value_of(self, term) -> int:
        z3 = self._z3
        if not z3.is_expr(term):
            return int(term)
        if self._model is None:
            return 0
        evaluated = self._model.eval(term, model_completion=True)
        if z3.is_bool(evaluated) or (z3.is_expr(term) and z3.is_bool(term)):
            return 1 if z3.is_true(evaluated) else 0
        try:
            return int(evaluated.as_long())
        except Exception:
            return 0

    def is_determined(self, term) -> bool:
        z3 = self._z3
        if not z3.is_expr(term):
            return True
        if self._model is None:
            return False
        evaluated = self._model.eval(term, model_completion=False)
        return not (z3.is_const(evaluated) and evaluated.eq(term))


def decisive_var_types() -> tuple[VarType, ...]:
    return (VarType.NORMAL, VarType.CC)
