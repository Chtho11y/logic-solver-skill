"""Compile a parsed puzzle DSL program into z3 constraints.

The compiler walks the AST and lowers it to a list of z3 boolean expressions:

* every top-level expression statement asserts its (broadcast) boolean value;
* ``if cond: body`` lowers each constraint in ``body`` to ``Implies(cond, c)``
  (guards accumulate, so nested ``if``/``for`` compose correctly);
* ``for v in iterable: body`` unrolls the loop, binding ``v`` each iteration;
* ``x[region]`` extracts the quantities of variable ``x`` over ``region``'s
  points; broadcasting and predefined functions follow :mod:`values` /
  :mod:`builtins`.

z3 is imported lazily so the rest of the package works without it installed.
UI-independent (no PyQt import).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..grid import Grid
from ..models import Point, PointKind, Variable, VarType
from . import ast_nodes as ast
from .builtins import BUILTIN_FUNCTIONS, BuiltinFunction, make_constants
from .errors import CompileError
from .parser import parse
from .values import (
    BroadcastError,
    RegionValue,
    VarValue,
    broadcast,
    flatten_scalars,
    map_elementwise,
    sort_points,
)


@dataclass
class _BoundMethod:
    """A value-bound method (e.g. ``list.append``) produced by member access."""

    name: str
    fn: Any  # Callable[[list, node], Any]


@dataclass
class UserFunction:
    """A ``def`` declared in the program (or an imported module)."""

    name: str
    params: list[str]
    body: list
    module: str = ""


class _ReturnSignal(Exception):
    """Internal control flow for ``return`` inside a ``def`` body."""

    def __init__(self, value: Any) -> None:
        self.value = value
        super().__init__("return")


@dataclass
class CompiledProgram:
    constraints: list  # list[z3.BoolRef]
    var_z3: dict[str, dict[Point, Any]]
    variables: list[Variable]
    grid: Grid
    # variable name -> {"id": {point: z3}, "size": {point: z3}} (lazily filled)
    cc_z3: dict[str, dict[str, dict[Point, Any]]] = field(default_factory=dict)
    # Debug lines emitted by print() during compilation.
    debug: list[str] = field(default_factory=list)
    # Extra named quantities produced by helper builtins (echoed to the UI).
    derived: dict[str, dict[Point, Any]] = field(default_factory=dict)
    derived_kinds: dict[str, PointKind] = field(default_factory=dict)


def _point_label(point: Point) -> str:
    if len(point) == 2:
        return f"r{point[0]}c{point[1]}"
    return f"{point[0]}{point[1]}_{point[2]}"


def compile_source(
    source: str,
    grid: Grid,
    variables,
    regions,
    z3,
    params: dict | None = None,
    loader: Callable[[str], str] | None = None,
    module: str = "<main>",
) -> CompiledProgram:
    """Parse ``source`` and compile it against the given editor state.

    ``params`` exposes puzzle instance data to ``param("name")`` and ``loader``
    resolves ``import "module"`` statements to source text.
    """

    program = parse(source)
    program.module = module
    return Compiler(grid, variables, regions, z3, params, loader).compile(program)


class Compiler:
    def __init__(
        self,
        grid: Grid,
        variables,
        regions,
        z3,
        params: dict | None = None,
        loader: Callable[[str], str] | None = None,
    ) -> None:
        self.grid = grid
        self.z3 = z3
        self.variables = list(variables)
        self.params = dict(params or {})
        self._loader = loader
        self._imported: set[str] = set()
        self._functions: dict[str, UserFunction] = {}
        self._call_depth = 0
        self._aux_counter = 0
        self.derived: dict[str, dict[Point, Any]] = {}
        self.derived_kinds: dict[str, PointKind] = {}
        self._memo: dict[tuple, Any] = {}

        # One z3 Int per point of each variable's kind. Constant variables get
        # plain Python ints (their presets) instead of z3 quantities, and
        # cc (region-partition) variables use their own ints as region ids.
        self.var_z3: dict[str, dict[Point, Any]] = {}
        self._var_values: dict[str, VarValue] = {}
        self._cc_names: set[str] = set()
        self._const_names: set[str] = set()
        for var in self.variables:
            vtype = getattr(var, "var_type", VarType.NORMAL)
            if vtype is VarType.CONSTANT:
                quantities = {
                    p: int(v)
                    for p, v in getattr(var, "givens", {}).items()
                    if grid.contains(var.kind, p)
                }
                order = sort_points(quantities.keys())
                self.var_z3[var.name] = quantities
                self._var_values[var.name] = VarValue(var.name, var.kind, quantities, order)
                self._const_names.add(var.name)
                continue
            order = sort_points(grid.points(var.kind))
            quantities = {p: z3.Int(f"{var.name}#{_point_label(p)}") for p in order}
            self.var_z3[var.name] = quantities
            self._var_values[var.name] = VarValue(var.name, var.kind, quantities, order)
            if vtype is VarType.CC:
                self._cc_names.add(var.name)

        # User regions and grid-derived constants.
        self.region_list = [RegionValue.of(region.kind, region.points) for region in regions]
        self._region_values: dict[str, RegionValue] = {
            region.name: RegionValue.of(region.kind, region.points) for region in regions
        }
        self._constants = make_constants(grid)
        self._constants["regions"] = self.region_list

        self._scopes: list[dict[str, Any]] = []
        self._guards: list = []
        self._constraints: list = []
        self._debug: list[str] = []

        # Lazily-generated connected-component (cc) z3 variables, per variable
        # name: {"id": {point: z3}, "size": {point: z3}}.
        self._cc_z3: dict[str, dict[str, dict[Point, Any]]] = {}

    # -- entry ----------------------------------------------------------

    def compile(self, program: ast.Program) -> CompiledProgram:
        self._apply_variable_presets()
        self._exec_block(program.statements)
        # Always generate the connectivity for cc (region-partition) variables
        # so their region ids exist and can be echoed even if the program never
        # referenced them.
        for name in self._cc_names:
            self._ensure_cc(name)
        return CompiledProgram(
            self._constraints,
            self.var_z3,
            self.variables,
            self.grid,
            self._cc_z3,
            self._debug,
            self.derived,
            self.derived_kinds,
        )

    # -- aux variables (used by helper builtins) ------------------------

    def new_int(self, prefix: str) -> Any:
        """Allocate a fresh auxiliary z3 integer."""

        self._aux_counter += 1
        return self.z3.Int(f"{prefix}#{self._aux_counter}")

    def add_aux(self, constraint) -> None:
        """Add a definitional constraint that is *not* subject to ``if`` guards."""

        self._constraints.append(constraint)

    def memo(self, key: tuple, build):
        """Cache an expensive derived encoding (connectivity, loops, ...)."""

        if key not in self._memo:
            self._memo[key] = build()
        return self._memo[key]

    def publish(self, name: str, kind: PointKind, quantities: dict) -> None:
        """Expose derived quantities so the UI can render them."""

        self.derived[name] = quantities
        self.derived_kinds[name] = kind

    # -- debug ----------------------------------------------------------

    def add_debug(self, line: int, text: str) -> None:
        """Record a ``print()`` debug line (surfaced in the solver output)."""

        self._debug.append(f"line {line}: {text}")

    def _apply_variable_presets(self) -> None:
        """Assert each variable's value range (``domain``) and pinned givens.

        These are unconditional constraints (no ``if`` guards apply) added
        before the user program so ``x[...] == given`` and ``lo <= x <= hi``
        always hold.
        """

        for var in self.variables:
            # cc variables encode their own connectivity; constant variables
            # carry their values directly (no z3 quantities) -- neither takes a
            # domain or pinned givens here.
            if getattr(var, "var_type", VarType.NORMAL) is not VarType.NORMAL:
                continue
            quantities = self.var_z3[var.name]
            domain = getattr(var, "domain", None)
            if domain is not None:
                lo, hi = domain
                for q in quantities.values():
                    self._constraints.append(self.z3.And(q >= lo, q <= hi))
            for point, value in getattr(var, "givens", {}).items():
                q = quantities.get(point)
                if q is not None:
                    self._constraints.append(q == int(value))

    # -- statements -----------------------------------------------------

    def _exec_block(self, statements) -> None:
        # Declarations are hoisted so helpers may be used before their `def`.
        for stmt in statements:
            if isinstance(stmt, ast.DefStmt):
                self._functions[stmt.name] = UserFunction(stmt.name, list(stmt.params), stmt.body)
        for stmt in statements:
            if not isinstance(stmt, ast.DefStmt):
                self._exec_stmt(stmt)

    def _exec_stmt(self, stmt) -> None:
        if isinstance(stmt, ast.LetStmt):
            value = self._eval(stmt.expr)
            self._bind_targets(stmt.targets, value, stmt)
        elif isinstance(stmt, ast.ExprStmt):
            self._assert_value(self._eval(stmt.expr), stmt)
        elif isinstance(stmt, ast.IfStmt):
            self._exec_if(stmt)
        elif isinstance(stmt, ast.DefStmt):
            self._functions[stmt.name] = UserFunction(stmt.name, list(stmt.params), stmt.body)
        elif isinstance(stmt, ast.ReturnStmt):
            value = self._eval(stmt.expr) if stmt.expr is not None else []
            if self._call_depth == 0:
                raise CompileError("'return' outside of a def", stmt.line, stmt.col)
            raise _ReturnSignal(value)
        elif isinstance(stmt, ast.ImportStmt):
            self._exec_import(stmt)
        elif isinstance(stmt, ast.ForStmt):
            items = self._iter_items(self._eval(stmt.iterable), stmt)
            for item in items:
                self._scopes.append({})
                try:
                    self._bind_targets(stmt.vars, item, stmt, local=True)
                    self._exec_block(stmt.body)
                finally:
                    self._scopes.pop()
        else:  # pragma: no cover - defensive
            raise CompileError("unknown statement", stmt.line, stmt.col)

    def _exec_import(self, stmt: ast.ImportStmt) -> None:
        name = stmt.path.strip()
        if name in self._imported:
            return
        if self._loader is None:
            raise CompileError("import is not available in this context", stmt.line, stmt.col)
        try:
            source = self._loader(name)
        except Exception as exc:
            raise CompileError(f"cannot import {name!r}: {exc}", stmt.line, stmt.col) from exc
        self._imported.add(name)
        try:
            program = parse(source)
        except CompileError:
            raise
        except Exception as exc:
            raise CompileError(f"in module {name!r}: {exc}", stmt.line, stmt.col) from exc
        # Imported modules execute at global scope so their defs are shared.
        saved_scopes, self._scopes = self._scopes, []
        try:
            self._exec_block(program.statements)
        finally:
            self._scopes = saved_scopes

    def _call_user_function(self, fn: UserFunction, args: list, node) -> Any:
        if len(args) != len(fn.params):
            raise CompileError(
                f"{fn.name}() takes {len(fn.params)} argument(s) but {len(args)} given",
                node.line,
                node.col,
            )
        if self._call_depth > 64:
            raise CompileError(f"{fn.name}(): recursion too deep", node.line, node.col)
        frame = dict(zip(fn.params, args))
        saved_scopes, self._scopes = self._scopes, [frame]
        self._call_depth += 1
        try:
            self._exec_block(fn.body)
            return []
        except _ReturnSignal as signal:
            return signal.value
        finally:
            self._call_depth -= 1
            self._scopes = saved_scopes

    # -- binding & control flow -----------------------------------------

    def _set_local(self, name: str, value: Any, local: bool = False) -> None:
        """Bind ``name``.

        ``let`` rebinds the nearest enclosing binding when one exists, so the
        accumulator idiom ``let total = total + ...`` inside a ``for`` body
        keeps working across iterations. Loop variables pass ``local=True`` and
        always live in the loop's own (per-iteration) scope.
        """

        if not self._scopes:
            self._scopes.append({})
        if not local:
            for scope in reversed(self._scopes):
                if name in scope:
                    scope[name] = value
                    return
        self._scopes[-1][name] = value

    def _bind_targets(self, targets, value, node, local: bool = False) -> None:
        """Bind a single value, or unpack it across several targets.

        ``let x = e`` / ``for x in e`` bind directly; the structured forms
        ``let a, b, c = e`` / ``for a, b, c in e`` require ``e`` (resp. each
        loop item) to yield exactly as many elements as there are targets.
        """

        if len(targets) == 1:
            self._set_local(targets[0], value, local)
            return
        items = self._iter_items(value, node)
        if len(items) != len(targets):
            raise CompileError(
                f"cannot unpack {len(items)} value(s) into {len(targets)} targets",
                node.line,
                node.col,
            )
        for name, item in zip(targets, items):
            self._set_local(name, item, local)

    def _exec_if(self, stmt: ast.IfStmt) -> None:
        cond_value = self._eval(stmt.cond)
        const = self._try_const_bool(cond_value)
        if const is not None:
            # Compile-time constant condition: emit only the taken branch and
            # add no guard/constraint for the condition itself.
            self._exec_block(stmt.body if const else stmt.orelse)
            return
        cond = self._to_single_bool(cond_value, stmt)
        self._guards.append(cond)
        try:
            self._exec_block(stmt.body)
        finally:
            self._guards.pop()
        if stmt.orelse:
            self._guards.append(self.z3.Not(cond))
            try:
                self._exec_block(stmt.orelse)
            finally:
                self._guards.pop()

    @staticmethod
    def _try_const_bool(value):
        """Return a Python bool if ``value`` is a compile-time constant boolean.

        Returns ``None`` when any part is a z3 expression (i.e. not constant).
        """

        items = flatten_scalars(value)
        if all(isinstance(item, bool) for item in items):
            return all(items)
        return None

    # -- assertions / guards --------------------------------------------

    def _assert_value(self, value: Any, node) -> None:
        for item in flatten_scalars(value):
            bool_expr = self._require_bool(item, node)
            self._constraints.append(self._apply_guards(bool_expr))

    def _apply_guards(self, bool_expr):
        if not self._guards:
            return bool_expr
        guard = self._and_all(self._guards)
        return self.z3.Implies(guard, bool_expr)

    def _to_single_bool(self, value: Any, node):
        bools = [self._require_bool(item, node) for item in flatten_scalars(value)]
        if not bools:
            return self.z3.BoolVal(True)
        if len(bools) == 1:
            return bools[0]
        return self._and_all(bools)

    def _and_all(self, items):
        return self.z3.And([self._as_bool(item) for item in items])

    def _as_bool(self, value):
        if isinstance(value, bool):
            return self.z3.BoolVal(value)
        return value

    def _require_bool(self, value, node):
        if isinstance(value, bool):
            return self.z3.BoolVal(value)
        if self.z3.is_expr(value) and self.z3.is_bool(value):
            return value
        raise CompileError("expected a boolean constraint here", node.line, node.col)

    def _iter_items(self, value, node) -> list:
        if isinstance(value, VarValue):
            return value.as_list()
        if isinstance(value, RegionValue):
            return [RegionValue.of(value.kind, [p]) for p in value.points]
        if isinstance(value, list):
            return list(value)
        raise CompileError("value is not iterable", node.line, node.col)

    # -- expressions ----------------------------------------------------

    def _eval(self, node) -> Any:
        if isinstance(node, ast.Num):
            return node.value
        if isinstance(node, ast.Bool):
            return node.value
        if isinstance(node, ast.Str):
            return node.value
        if isinstance(node, ast.Name):
            return self._eval_name(node)
        if isinstance(node, ast.ListLit):
            return [self._eval(item) for item in node.items]
        if isinstance(node, ast.Index):
            return self._eval_index(node)
        if isinstance(node, ast.Member):
            return self._eval_member(node)
        if isinstance(node, ast.Call):
            return self._eval_call(node)
        if isinstance(node, ast.Unary):
            return self._eval_unary(node)
        if isinstance(node, ast.Binary):
            return self._eval_binary(node)
        raise CompileError("cannot evaluate expression", node.line, node.col)  # pragma: no cover

    def _eval_name(self, node: ast.Name) -> Any:
        name = node.ident
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        if name in self._var_values:
            return self._var_values[name]
        if name in self._region_values:
            return self._region_values[name]
        if name in self._constants:
            return self._constants[name]
        if name in self._functions:
            return self._functions[name]
        if name in BUILTIN_FUNCTIONS:
            return BUILTIN_FUNCTIONS[name]
        raise CompileError(f"unknown name '{name}'", node.line, node.col)

    def _eval_index(self, node: ast.Index) -> Any:
        base = self._eval(node.base)
        index = self._eval(node.index)
        try:
            return self._do_index(base, index, node)
        except BroadcastError as exc:
            raise CompileError(str(exc), node.line, node.col) from exc

    def _do_index(self, base, index, node) -> Any:
        if isinstance(index, list):
            return [self._do_index(base, i, node) for i in index]

        if isinstance(base, VarValue):
            if isinstance(index, RegionValue):
                if index.kind is not base.kind:
                    raise CompileError(
                        f"variable '{base.name}' is bound to {base.kind.label.lower()} "
                        f"but indexed by a {index.kind.label.lower()} region",
                        node.line,
                        node.col,
                    )
                missing = [p for p in index.points if p not in base.quantities]
                if missing:
                    if base.name in self._const_names:
                        raise CompileError(
                            f"constant '{base.name}' has no value at the indexed point(s)",
                            node.line,
                            node.col,
                        )
                    raise CompileError("region point outside the grid", node.line, node.col)
                return [base.quantities[p] for p in index.points]
            if isinstance(index, bool) or not isinstance(index, int):
                raise CompileError("variable index must be a region or integer", node.line, node.col)
            if not 0 <= index < len(base.order):
                raise CompileError(f"index {index} out of range", node.line, node.col)
            return base.quantities[base.order[index]]

        if isinstance(base, RegionValue):
            idx = self._as_index_int(index, node)
            if not 0 <= idx < len(base.points):
                raise CompileError(f"index {idx} out of range", node.line, node.col)
            return RegionValue.of(base.kind, [base.points[idx]])

        if isinstance(base, list):
            idx = self._as_index_int(index, node)
            if not 0 <= idx < len(base):
                raise CompileError(f"index {idx} out of range", node.line, node.col)
            return base[idx]

        raise CompileError("value is not indexable", node.line, node.col)

    def _as_index_int(self, value, node) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise CompileError("index must be a concrete integer", node.line, node.col)
        return value

    # -- member access (connected components) ---------------------------

    def _eval_member(self, node: ast.Member) -> Any:
        base = self._eval(node.base)
        attr = node.attr
        if isinstance(base, list):
            return self._list_member(base, attr, node)
        if isinstance(base, RegionValue):
            if attr == "size":
                return len(base.points)
            raise CompileError(f"a region has no member '{attr}'", node.line, node.col)
        if isinstance(base, VarValue):
            if base.name in self._cc_names:
                return self._cc_member(base.name, attr, node)
            if attr == "size":
                return len(base.order)
            raise CompileError(f"'{base.name}' has no member '{attr}'", node.line, node.col)
        raise CompileError("value has no members", node.line, node.col)

    def _cc_member(self, name: str, attr: str, node) -> Any:
        """Resolve ``.id`` / ``.size`` / ``.border`` of a cc variable."""

        if attr == "id":
            self._ensure_cc(name)
            return self._var_values[name]  # the per-cell region ids themselves
        if attr == "size":
            self._ensure_cc_size(name)
            return self._cc_var_value(name, "size", PointKind.CELL)
        if attr == "border":
            self._ensure_cc_border(name)
            return self._cc_var_value(name, "border", PointKind.EDGE)
        raise CompileError(
            f"region variable '{name}' has no member '{attr}' (use id/size/border)",
            node.line,
            node.col,
        )

    def _list_member(self, base: list, attr: str, node) -> Any:
        if attr == "size":
            return len(base)
        if attr == "append":
            return _BoundMethod("append", lambda args, n: self._list_append(base, args, n))
        raise CompileError(f"a list has no member '{attr}'", node.line, node.col)

    def _list_append(self, base: list, args: list, node) -> list:
        if len(args) != 1:
            raise CompileError("append(x) takes exactly one argument", node.line, node.col)
        # Return a new list (no in-place mutation of the bound value).
        return list(base) + [args[0]]

    def _cc_var_value(self, name: str, member: str, kind: PointKind) -> VarValue:
        quantities = self._cc_z3[name][member]
        order = sort_points(quantities.keys())
        return VarValue(f"{name}.{member}", kind, quantities, order)

    def _ensure_cc(self, name: str) -> None:
        """Generate the cc connectivity constraints for region variable ``name``.

        Idempotent (cached per variable name). The variable's own per-cell
        quantities *are* the region ids. Encodes, over the 4-connected grid:
        every region's ``id`` equals the minimum linear index ``r*cols+c`` of
        its cells (its unique root), and cells sharing an ``id`` are necessarily
        connected (a spanning-tree distance witness).
        """

        if name in self._cc_z3:
            return
        z3 = self.z3
        cols = self.grid.cols
        cells = sort_points(self.grid.cells())
        cell_set = set(cells)
        # The cc variable's own quantities serve as the region ids.
        id_vars: dict[Point, Any] = self.var_z3[name]
        dist_vars: dict[Point, Any] = {
            (r, c): z3.Int(f"{name}#cc_dist#r{r}c{c}") for (r, c) in cells
        }
        deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))
        for (r, c) in cells:
            lin = r * cols + c
            idc = id_vars[(r, c)]
            dc = dist_vars[(r, c)]
            self._constraints.append(z3.And(idc >= 0, idc <= lin))
            self._constraints.append(dc >= 0)
            # A cell is its region's root iff its distance is zero.
            self._constraints.append((dc == 0) == (idc == lin))
            # Non-root cells must have a 4-neighbour one step closer to the root
            # with the same id (this is what forces same-id cells to connect).
            neighbours = [(r + dr, c + dcol) for dr, dcol in deltas if (r + dr, c + dcol) in cell_set]
            parents = [
                z3.And(id_vars[n] == idc, dist_vars[n] == dc - 1) for n in neighbours
            ]
            parent_exists = z3.Or(parents) if parents else z3.BoolVal(False)
            self._constraints.append(z3.Implies(dc > 0, parent_exists))
        self._cc_z3[name] = {"id": id_vars, "_dist": dist_vars}

    def _ensure_cc_size(self, name: str) -> None:
        """Generate cc.size z3 vars: the count of cells sharing each id.

        O(N^2) in the number of cells (an ``If`` sum per cell); only emitted
        when ``.size`` is actually referenced. Cached per variable name.
        """

        self._ensure_cc(name)
        cc = self._cc_z3[name]
        if "size" in cc:
            return
        z3 = self.z3
        id_vars = cc["id"]
        cells = sort_points(id_vars.keys())
        size_vars: dict[Point, Any] = {
            p: z3.Int(f"{name}#cc_size#r{p[0]}c{p[1]}") for p in cells
        }
        for p in cells:
            terms = [z3.If(id_vars[d] == id_vars[p], 1, 0) for d in cells]
            self._constraints.append(size_vars[p] == z3.Sum(terms))
        cc["size"] = size_vars

    def _ensure_cc_border(self, name: str) -> None:
        """Generate cc.border z3 vars: a 0/1 integer per edge.

        ``border(e) == 1`` iff the edge is on the grid boundary, or the two
        cells it separates lie in different regions (different cc ids). Cached
        per variable name; only emitted when ``.border`` is referenced.
        """

        self._ensure_cc(name)
        cc = self._cc_z3[name]
        if "border" in cc:
            return
        z3 = self.z3
        id_vars = cc["id"]
        edges = sort_points(self.grid.edges())
        border_vars: dict[Point, Any] = {}
        for edge in edges:
            orient, er, ec = edge
            b = z3.Int(f"{name}#cc_border#{orient}{er}_{ec}")
            border_vars[edge] = b
            self._constraints.append(z3.Or(b == 0, b == 1))
            sides = self._edge_cells(edge)
            if len(sides) < 2:
                # Edge on the grid boundary: always a border.
                self._constraints.append(b == 1)
            else:
                a, d = sides
                self._constraints.append((b == 1) == (id_vars[a] != id_vars[d]))
        cc["border"] = border_vars

    def _edge_cells(self, edge: Point) -> list:
        """The (in-grid) cells on either side of an edge."""

        orient, r, c = edge
        if orient == "H":
            cands = [(r - 1, c), (r, c)]
        else:
            cands = [(r, c - 1), (r, c)]
        return [
            (cr, cc)
            for cr, cc in cands
            if 0 <= cr < self.grid.rows and 0 <= cc < self.grid.cols
        ]

    def _eval_call(self, node: ast.Call) -> Any:
        callee = self._eval(node.callee)
        args = [self._eval(arg) for arg in node.args]
        if isinstance(callee, UserFunction):
            return self._call_user_function(callee, args, node)
        if isinstance(callee, _BoundMethod):
            try:
                return callee.fn(args, node)
            except BroadcastError as exc:
                raise CompileError(str(exc), node.line, node.col) from exc
        if not isinstance(callee, BuiltinFunction):
            raise CompileError("value is not callable", node.line, node.col)
        try:
            if callee.elementwise:
                if len(args) != 1:
                    raise CompileError(f"{callee.name}() takes exactly one argument", node.line, node.col)
                return map_elementwise(args[0], lambda v: callee.fn(self, v))
            # Broadcast: a function declared to take a single point/region,
            # called with a List[X], is applied once per element.
            if callee.broadcast and len(args) == 1 and isinstance(args[0], list):
                return [callee.fn(self, [item], node) for item in args[0]]
            return callee.fn(self, args, node)
        except BroadcastError as exc:
            raise CompileError(str(exc), node.line, node.col) from exc

    def _eval_unary(self, node: ast.Unary) -> Any:
        operand = self._eval(node.operand)
        try:
            if node.op == "not":
                return map_elementwise(operand, self._not)
            if node.op == "-":
                return map_elementwise(operand, lambda v: -v)
            return map_elementwise(operand, lambda v: v)  # unary '+'
        except BroadcastError as exc:
            raise CompileError(str(exc), node.line, node.col) from exc

    def _not(self, value):
        # Keep compile-time booleans concrete so `if` can constant-fold.
        if isinstance(value, bool):
            return not value
        return self.z3.Not(self._as_bool(value))

    def _eval_binary(self, node: ast.Binary) -> Any:
        op = node.op
        if op in ("and", "or", "xor", "implies"):
            left = self._eval(node.left)
            right = self._eval(node.right)
            # ``list and list`` (or any two collections) merges them.
            if op == "and" and self._is_mergeable(left) and self._is_mergeable(right):
                return self._merge(left, right, node)
            fn = {
                "and": self._logic_and,
                "or": self._logic_or,
                "xor": self._logic_xor,
                "implies": self._logic_implies,
            }[op]
            return self._combine(left, right, fn, node)

        left = self._eval(node.left)
        right = self._eval(node.right)
        fn = self._ARITH.get(op)
        if fn is None:  # pragma: no cover - parser guards this
            raise CompileError(f"unknown operator '{op}'", node.line, node.col)
        return self._combine(left, right, lambda a, b: fn(self, a, b, node), node)

    # -- collection merge (``and`` on lists/regions) --------------------

    @staticmethod
    def _is_mergeable(value) -> bool:
        return isinstance(value, (list, RegionValue, VarValue))

    def _merge(self, left, right, node):
        if isinstance(left, RegionValue) and isinstance(right, RegionValue):
            if left.kind is right.kind:
                return RegionValue.of(left.kind, list(left.points) + list(right.points))
            raise CompileError(
                "cannot merge regions of different kinds", node.line, node.col
            )
        return self._as_merge_list(left) + self._as_merge_list(right)

    @staticmethod
    def _as_merge_list(value) -> list:
        if isinstance(value, list):
            return list(value)
        if isinstance(value, RegionValue):
            return [RegionValue.of(value.kind, [p]) for p in value.points]
        if isinstance(value, VarValue):
            return value.as_list()
        return [value]

    def _combine(self, left, right, fn, node):
        try:
            return broadcast(left, right, fn)
        except BroadcastError as exc:
            raise CompileError(str(exc), node.line, node.col) from exc

    # -- scalar operator implementations --------------------------------

    def _logic_and(self, a, b):
        if isinstance(a, bool) and isinstance(b, bool):
            return a and b
        return self.z3.And(self._as_bool(a), self._as_bool(b))

    def _logic_or(self, a, b):
        if isinstance(a, bool) and isinstance(b, bool):
            return a or b
        return self.z3.Or(self._as_bool(a), self._as_bool(b))

    def _logic_xor(self, a, b):
        if isinstance(a, bool) and isinstance(b, bool):
            return a != b
        return self.z3.Xor(self._as_bool(a), self._as_bool(b))

    def _logic_implies(self, a, b):
        if isinstance(a, bool) and isinstance(b, bool):
            return (not a) or b
        return self.z3.Implies(self._as_bool(a), self._as_bool(b))

    @staticmethod
    def _op_add(self, a, b, node):
        return a + b

    @staticmethod
    def _op_sub(self, a, b, node):
        return a - b

    @staticmethod
    def _op_mul(self, a, b, node):
        return a * b

    @staticmethod
    def _op_div(self, a, b, node):
        if isinstance(a, int) and isinstance(b, int):
            if b == 0:
                raise CompileError("division by zero", node.line, node.col)
            return a // b
        return a / b

    @staticmethod
    def _op_mod(self, a, b, node):
        if isinstance(a, int) and isinstance(b, int):
            if b == 0:
                raise CompileError("modulo by zero", node.line, node.col)
            return a % b
        return a % b

    @staticmethod
    def _op_eq(self, a, b, node):
        return a == b

    @staticmethod
    def _op_ne(self, a, b, node):
        return a != b

    @staticmethod
    def _op_lt(self, a, b, node):
        return a < b

    @staticmethod
    def _op_le(self, a, b, node):
        return a <= b

    @staticmethod
    def _op_gt(self, a, b, node):
        return a > b

    @staticmethod
    def _op_ge(self, a, b, node):
        return a >= b

    _ARITH = {
        "+": _op_add.__func__,
        "-": _op_sub.__func__,
        "*": _op_mul.__func__,
        "/": _op_div.__func__,
        "%": _op_mod.__func__,
        "==": _op_eq.__func__,
        "!=": _op_ne.__func__,
        "<": _op_lt.__func__,
        "<=": _op_le.__func__,
        ">": _op_gt.__func__,
        ">=": _op_ge.__func__,
    }
