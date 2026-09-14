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
from .features import BackendFeatures, features_for
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
        config.use_graph_division_primitive = (
            resolved == "cspuz_core" and "graph_division" in info.features
        )
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


def _convert_z3_expr(expr: Any, variables_dict: dict) -> Any:
    """cspuz Z3 conversion plus BOOL_CONSTANT / INT_CONSTANT.

    Upstream ``cspuz.backend.z3._convert_expr`` falls through on those ops and
    returns ``None``, which Z3 then rejects. ``fold_and`` / ``fold_or`` emit
    them for tautologies such as a 1×1 ``cloop`` with no inner edges.
    """

    import z3
    from cspuz.expr import BoolVar, Expr, IntVar, Op

    if isinstance(expr, (bool, int)):
        return expr
    if not isinstance(expr, Expr):
        raise TypeError(f"cannot convert {type(expr).__name__} to Z3")
    if isinstance(expr, (BoolVar, IntVar)):
        return variables_dict[expr.id]
    if expr.op == Op.BOOL_CONSTANT:
        return bool(expr.operands[0])
    if expr.op == Op.INT_CONSTANT:
        return int(expr.operands[0])
    operands = [_convert_z3_expr(item, variables_dict) for item in expr.operands]
    if expr.op == Op.NEG:
        return -operands[0]
    if expr.op == Op.ADD:
        total = operands[0]
        for item in operands[1:]:
            total = total + item
        return total
    if expr.op == Op.SUB:
        total = operands[0]
        for item in operands[1:]:
            total = total - item
        return total
    if expr.op == Op.EQ:
        return operands[0] == operands[1]
    if expr.op == Op.NE:
        return operands[0] != operands[1]
    if expr.op == Op.LE:
        return operands[0] <= operands[1]
    if expr.op == Op.LT:
        return operands[0] < operands[1]
    if expr.op == Op.GE:
        return operands[0] >= operands[1]
    if expr.op == Op.GT:
        return operands[0] > operands[1]
    if expr.op == Op.NOT:
        return z3.Not(operands[0])
    if expr.op == Op.AND:
        return z3.And(operands)
    if expr.op == Op.OR:
        return z3.Or(operands)
    if expr.op == Op.XOR:
        return z3.Xor(operands[0], operands[1])
    if expr.op == Op.IFF:
        return operands[0] == operands[1]
    if expr.op == Op.IMP:
        return z3.Or(z3.Not(operands[0]), operands[1])
    if expr.op == Op.IF:
        return z3.If(operands[0], operands[1], operands[2])
    if expr.op == Op.ALLDIFF:
        return z3.Distinct(operands)
    raise BackendError(f"unsupported cspuz operator for Z3: {expr.op}")


def _timed_z3_backend(timeout_ms: int | None) -> type:
    """Build a cspuz backend class that preserves Z3 timeout/unknown states."""

    from cspuz.backend.z3 import Z3Backend
    from cspuz.expr import BoolVar, IntVar

    class TimedZ3Backend(Z3Backend):
        def add_constraint(self, constraint):  # noqa: ANN001
            import z3

            items = constraint if isinstance(constraint, list) else [constraint]
            for item in items:
                converted = _convert_z3_expr(item, self.variables_dict)
                if converted is True:
                    continue
                if converted is False:
                    self.converted_constraints.append(z3.BoolVal(False))
                    continue
                self.converted_constraints.append(converted)

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

    def __init__(
        self,
        backend: str = "z3",
        features: BackendFeatures | None = None,
    ) -> None:
        import cspuz

        self.backend = backend
        self.features = features if features is not None else features_for(backend)
        self.solver = cspuz.Solver()
        self._const_one = None

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

    def _bool_like(self, value: Any) -> Any:
        """Lift a Python bool so it can sit next to cspuz BoolExpr operands."""

        if not isinstance(value, bool):
            return value
        if self._const_one is None:
            self._const_one = self.Int("_const_one", 1, 1)
        return (self._const_one == 1) if value else (self._const_one == 0)

    def vertices_connected(
        self,
        is_active: Any,
        edges: Any,
    ) -> Any:
        """At most one connected component of active vertices; empty is allowed."""

        flags = [self._bool_like(flag) for flag in is_active]
        edge_list = [(int(u), int(v)) for u, v in edges]
        n = len(flags)
        if n == 0:
            return self.BoolVal(True)
        if self.features.graph_vertex_connected:
            return self._vertices_connected_primitive(flags, edge_list)
        return self._vertices_connected_expanded(flags, edge_list)

    def _vertices_connected_primitive(
        self, flags: list, edges: list[tuple[int, int]]
    ) -> Any:
        from cspuz.expr import BoolExpr, Op

        operands: list[Any] = [len(flags), len(edges)]
        operands.extend(flags)
        for u, v in edges:
            operands.extend((u, v))
        return BoolExpr(Op.GRAPH_ACTIVE_VERTICES_CONNECTED, operands)

    def _vertices_connected_expanded(
        self, flags: list, edges: list[tuple[int, int]]
    ) -> Any:
        n = len(flags)
        adj: list[list[int]] = [[] for _ in range(n)]
        for u, v in edges:
            adj[u].append(v)
            adj[v].append(u)
        rank = [self.Int(f"avc#rank#{i}", 0, max(0, n - 1)) for i in range(n)]
        is_root = [self.Int(f"avc#root#{i}", 0, 1) for i in range(n)]
        parts = []
        for i in range(n):
            active = flags[i]
            root = is_root[i] == 1
            parts.append(self.Implies(root, active))
            choices = [root]
            for j in adj[i]:
                choices.append(self.And(flags[j], rank[j] < rank[i]))
            parts.append(self.Implies(active, self.Or(*choices)))
        parts.append(self.Sum([self.If(is_root[i] == 1, 1, 0) for i in range(n)]) <= 1)
        return self.And(*parts)

    def edges_single_cycle(
        self,
        is_active: Any,
        pairs: Any,
        n_vertices: int,
        *,
        nonempty: bool = True,
    ) -> Any:
        """Selected edges form exactly one simple cycle (or none, if allowed)."""

        flags = [self._bool_like(flag) for flag in is_active]
        edge_pairs = [(int(u), int(v)) for u, v in pairs]
        n = int(n_vertices)
        if n == 0:
            return self.BoolVal(not nonempty)
        incident: list[list[int]] = [[] for _ in range(n)]
        for eid, (u, v) in enumerate(edge_pairs):
            incident[u].append(eid)
            incident[v].append(eid)
        degree_ok = []
        passed = []
        for vertex in range(n):
            if incident[vertex]:
                deg = self.Sum([self.If(flags[eid], 1, 0) for eid in incident[vertex]])
            else:
                deg = 0
            degree_ok.append(self.Or(deg == 0, deg == 2))
            passed.append(deg == 2)
        connected = self.vertices_connected(flags, _line_graph_pairs(incident))
        parts = list(degree_ok)
        parts.append(connected)
        if nonempty:
            parts.append(self.Sum([self.If(flag, 1, 0) for flag in passed]) >= 1)
        return self.And(*parts)

    def edges_connected(
        self,
        is_active: Any,
        pairs: Any,
        n_vertices: int,
        *,
        nonempty: bool = True,
    ) -> Any:
        """Selected edges form a single connected component (ignoring isolates)."""

        flags = [self._bool_like(flag) for flag in is_active]
        edge_pairs = [(int(u), int(v)) for u, v in pairs]
        n = int(n_vertices)
        if edge_pairs:
            n = max(n, 1 + max(max(u, v) for u, v in edge_pairs))
        incident: list[list[int]] = [[] for _ in range(n)]
        for eid, (u, v) in enumerate(edge_pairs):
            incident[u].append(eid)
            incident[v].append(eid)
        connected = self.vertices_connected(flags, _line_graph_pairs(incident))
        if not nonempty:
            return connected
        if not flags:
            return self.BoolVal(False)
        return self.And(connected, self.Sum([self.If(flag, 1, 0) for flag in flags]) >= 1)

    def vertices_isolated_and_complement_connected(
        self,
        is_active: Any,
        pairs: Any,
        shape: tuple[int, int] | None = None,
    ) -> Any:
        """Active vertices are pairwise non-adjacent; the complement is connected.

        Backends with graph primitives use native vertex-connectivity on the
        complement plus a direct adjacency ban. Z3 uses cspuz's diagonal-rank
        encoding, which the upstream docs report is stronger than the two
        constraints separately when graph operators are unavailable.
        """

        flags = [self._bool_like(flag) for flag in is_active]
        edge_pairs = [(int(u), int(v)) for u, v in pairs]
        isolated = self._vertices_not_adjacent(flags, edge_pairs)
        if self.features.graph_vertex_connected or shape is None:
            complement = [self.Not(flag) for flag in flags]
            return self.And(isolated, self.vertices_connected(complement, edge_pairs))
        return self.And(isolated, self._blacks_do_not_segment(flags, shape))

    def _vertices_not_adjacent(self, flags: list, pairs: list[tuple[int, int]]) -> Any:
        if not pairs:
            return self.BoolVal(True)
        return self.And(
            *[self.Not(self.And(flags[u], flags[v])) for u, v in pairs]
        )

    def _blacks_do_not_segment(self, flags: list, shape: tuple[int, int]) -> Any:
        """Port of cspuz ``active_vertices_not_adjacent_and_not_segmenting``."""

        height, width = int(shape[0]), int(shape[1])
        if height * width != len(flags):
            raise BackendError(
                "island encoding needs one flag per cell in row-major order"
            )
        n = height * width
        rank = [self.Int(f"island#rank#{i}", 0, max(0, (n - 1) // 2)) for i in range(n)]
        parts = []
        for y in range(height):
            for x in range(width):
                i = y * width + x
                less = []
                touches_outside = False
                for dy in (-1, 1):
                    for dx in (-1, 1):
                        y2, x2 = y + dy, x + dx
                        if 0 <= y2 < height and 0 <= x2 < width:
                            j = y2 * width + x2
                            less.append(self.And(rank[j] < rank[i], flags[j]))
                            if (y2, x2) < (y, x):
                                parts.append(rank[j] != rank[i])
                        else:
                            touches_outside = True
                limit = 0 if touches_outside else 1
                if less:
                    count = self.Sum([self.If(term, 1, 0) for term in less])
                else:
                    count = 0
                parts.append(self.Implies(flags[i], count <= limit))
        return self.And(*parts) if parts else self.BoolVal(True)


def _line_graph_pairs(incident: list[list[int]]) -> list[tuple[int, int]]:
    """Edges of the line graph: original edges adjacent iff they share a vertex."""

    seen: set[tuple[int, int]] = set()
    out: list[tuple[int, int]] = []
    for eids in incident:
        for i, left in enumerate(eids):
            for right in eids[:i]:
                a, b = (left, right) if left < right else (right, left)
                if (a, b) not in seen:
                    seen.add((a, b))
                    out.append((a, b))
    return out


def create_model(backend: str = "auto") -> CspuzModel:
    resolved = backend
    if backend == "auto":
        try:
            resolved = resolve_backend("auto")
        except BackendError:
            resolved = "z3"
    return CspuzModel(backend=resolved, features=features_for(resolved))
