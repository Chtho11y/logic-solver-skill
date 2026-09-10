"""cspuz implementation of the DSL constraint-model protocol."""

from __future__ import annotations

import os
import subprocess
import threading
from contextlib import contextmanager
from typing import Any, Iterator

from .base import (
    BackendError,
    BackendTimeoutError,
    BackendUnknownError,
    ConstraintModel,
)
from .registry import backend_info, resolve_backend

_CONFIG_LOCK = threading.RLock()


@contextmanager
def backend_configuration(
    backend: str, timeout_ms: int | None = None
) -> Iterator[str]:
    """Temporarily configure cspuz for one concrete backend."""

    import cspuz

    resolved = resolve_backend(backend, timeout_ms=timeout_ms)
    with _CONFIG_LOCK:
        config = cspuz.config
        old = (
            config.default_backend,
            config.use_graph_primitive,
            config.use_graph_division_primitive,
            config.solver_timeout,
            config.backend_path,
        )
        info = backend_info(resolved)
        config.default_backend = resolved
        config.use_graph_primitive = info.supports_graph_primitives
        config.use_graph_division_primitive = resolved == "cspuz_core"
        config.solver_timeout = None if timeout_ms is None else timeout_ms / 1000.0
        configured_path = os.environ.get("CSPUZ_BACKEND_PATH")
        if configured_path:
            config.backend_path = configured_path
        try:
            yield resolved
        finally:
            (
                config.default_backend,
                config.use_graph_primitive,
                config.use_graph_division_primitive,
                config.solver_timeout,
                config.backend_path,
            ) = old


def _timed_z3_backend(timeout_ms: int | None) -> type:
    """Build a cspuz backend class that preserves Z3 timeout/unknown states."""

    from cspuz.backend.z3 import Z3Backend
    from cspuz.expr import BoolVar, IntVar

    class TimedZ3Backend(Z3Backend):
        def solve(self) -> bool:
            import z3

            solver = z3.Solver()
            if timeout_ms is not None:
                solver.set("timeout", max(1, int(timeout_ms)))
            for var in self.variables:
                if isinstance(var, IntVar):
                    z3_var = self.variables_dict[var.id]
                    solver.add(var.lo <= z3_var, z3_var <= var.hi)
            solver.add(self.converted_constraints)

            check = solver.check()
            if check == z3.unsat:
                return False
            if check == z3.unknown:
                reason = solver.reason_unknown()
                if "timeout" in reason.lower():
                    raise BackendTimeoutError("Z3 solver timed out")
                raise BackendUnknownError(f"Z3 returned unknown: {reason}")

            model = solver.model()
            for var in self.variables:
                z3_var = self.variables_dict[var.id]
                evaluated = model.eval(z3_var, model_completion=True)
                if isinstance(var, BoolVar):
                    var.sol = z3.is_true(evaluated)
                else:
                    var.sol = evaluated.as_long()
            return True

    return TimedZ3Backend


class CspuzModel(ConstraintModel):
    """Constraint expression factory plus the owning cspuz ``Solver``."""

    def __init__(self) -> None:
        import cspuz

        self.solver = cspuz.Solver()

    def Int(
        self, name: str, lo: int | None = None, hi: int | None = None
    ) -> Any:
        del name  # cspuz variables are identified by stable numeric IDs.
        if lo is None or hi is None:
            raise BackendError("cspuz integer variables require finite bounds")
        return self.solver.int_var(int(lo), int(hi))

    @staticmethod
    def BoolVal(value: bool) -> bool:
        return bool(value)

    @staticmethod
    def Sum(values: Any) -> Any:
        from cspuz.constraints import flatten_iterator

        return sum(flatten_iterator(values), 0)

    @staticmethod
    def Distinct(values: Any) -> Any:
        import cspuz

        return cspuz.alldifferent(values)

    @staticmethod
    def And(*values: Any) -> Any:
        import cspuz

        return cspuz.fold_and(*values)

    @staticmethod
    def Or(*values: Any) -> Any:
        import cspuz

        return cspuz.fold_or(*values)

    @staticmethod
    def Not(value: Any) -> Any:
        return not value if isinstance(value, bool) else ~value

    @staticmethod
    def Xor(left: Any, right: Any) -> Any:
        if isinstance(left, bool) and isinstance(right, bool):
            return left != right
        return left != right

    @staticmethod
    def Implies(left: Any, right: Any) -> Any:
        if isinstance(left, bool):
            return right if left else True
        from cspuz.constraints import then

        return then(left, right)

    @staticmethod
    def If(condition: Any, when_true: Any, when_false: Any) -> Any:
        if isinstance(condition, bool):
            return when_true if condition else when_false
        from cspuz.expr import BoolExpr

        if isinstance(when_true, (bool, BoolExpr)) and isinstance(
            when_false, (bool, BoolExpr)
        ):
            return CspuzModel.Or(
                CspuzModel.And(condition, when_true),
                CspuzModel.And(CspuzModel.Not(condition), when_false),
            )
        import cspuz

        return cspuz.cond(condition, when_true, when_false)

    @staticmethod
    def is_expr(value: Any) -> bool:
        from cspuz.expr import Expr

        return isinstance(value, Expr)

    @staticmethod
    def is_bool(value: Any) -> bool:
        from cspuz.expr import BoolExpr

        return isinstance(value, BoolExpr)

    @staticmethod
    def bounds(value: Any) -> tuple[int, int] | None:
        """Infer an exact interval from cspuz's linear expression tree."""

        if isinstance(value, int) and not isinstance(value, bool):
            return value, value

        from cspuz.expr import IntExpr, IntVar, Op

        if isinstance(value, IntVar):
            return value.lo, value.hi
        if not isinstance(value, IntExpr):
            return None

        operands = value.operands
        if value.op == Op.NEG:
            inner = CspuzModel.bounds(operands[0])
            return None if inner is None else (-inner[1], -inner[0])
        if value.op in (Op.ADD, Op.SUB):
            left = CspuzModel.bounds(operands[0])
            right = CspuzModel.bounds(operands[1])
            if left is None or right is None:
                return None
            if value.op == Op.ADD:
                return left[0] + right[0], left[1] + right[1]
            return left[0] - right[1], left[1] - right[0]
        if value.op == Op.IF:
            when_true = CspuzModel.bounds(operands[1])
            when_false = CspuzModel.bounds(operands[2])
            if when_true is None or when_false is None:
                return None
            return (
                min(when_true[0], when_false[0]),
                max(when_true[1], when_false[1]),
            )
        return None

    def add_constraints(self, constraints: Any) -> None:
        self.solver.ensure(constraints)

    def find_answer(self, backend: str, timeout_ms: int | None = None) -> bool:
        with backend_configuration(backend, timeout_ms) as resolved:
            concrete: str | type
            concrete = (
                _timed_z3_backend(timeout_ms) if resolved == "z3" else resolved
            )
            try:
                return self.solver.find_answer(concrete)
            except subprocess.TimeoutExpired as exc:
                raise BackendTimeoutError(
                    f"solver backend {resolved!r} timed out"
                ) from exc

    @staticmethod
    def value(variable: Any) -> int | bool | None:
        if isinstance(variable, (int, bool)):
            return variable
        return getattr(variable, "sol", None)


def create_model() -> CspuzModel:
    return CspuzModel()
