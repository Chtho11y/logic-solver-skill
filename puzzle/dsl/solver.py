"""Solve a puzzle DSL program against an editor state using z3.

This is the single entry point the UI calls. z3 is imported lazily so the
editor keeps working (with solving disabled) when the optional ``z3-solver``
dependency is not installed.

UI-independent (no PyQt import).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..grid import Grid
from ..models import Point, PointKind
from .errors import DSLError

# Result status strings.
STATUS_SAT = "sat"
STATUS_UNSAT = "unsat"
STATUS_UNKNOWN = "unknown"
STATUS_ERROR = "error"
STATUS_COMPILED = "compiled"

# Fixed list of solver backends offered in the UI. "AUTO" lets z3 pick the
# tactic via ``z3.Solver()``; every other entry is passed to
# ``z3.SolverFor(logic)`` to select a specialized logic engine.
SOLVER_LOGICS: tuple[str, ...] = (
    "AUTO",
    "QF_LIA",
    "QF_FD",
    "QF_IDL",
    "LIA",
    "QF_NIA",
)


@dataclass
class SolveResult:
    status: str
    message: str = ""
    constraint_count: int = 0
    # name -> {point: int}
    values: dict[str, dict[Point, int]] = field(default_factory=dict)
    # name -> PointKind, for echoing onto the board.
    kinds: dict[str, PointKind] = field(default_factory=dict)
    error_line: int | None = None
    # Debug lines emitted by print() during compilation.
    debug: list[str] = field(default_factory=list)
    witnesses: list[tuple[str, int]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == STATUS_SAT


def is_available() -> bool:
    """Whether the z3 solver backend can be imported."""

    try:
        import z3  # noqa: F401
    except Exception:
        return False
    return True


def solve(
    grid: Grid,
    variables,
    regions,
    source: str,
    logic: str = "AUTO",
    params: dict | None = None,
    loader: Callable[[str], str] | None = None,
    timeout_ms: int | None = None,
    run_meta: bool = False,
) -> SolveResult:
    """Compile ``source`` and solve it; return a structured result.

    ``logic`` selects the z3 backend: ``"AUTO"`` (default) uses the general
    ``z3.Solver()``; any other value is passed to ``z3.SolverFor(logic)`` to
    pick a specialized logic engine. ``params`` feeds ``param("name")`` and
    ``loader`` resolves ``import "module"``. ``run_meta`` executes ``meta:``
    blocks during compilation (default off).
    """

    try:
        import z3
    except Exception:
        return SolveResult(
            STATUS_ERROR,
            "z3 is not installed. Run `pip install z3-solver` to enable solving.",
        )

    from .compiler import compile_source
    from .session import Z3Session

    session = Z3Session(z3, timeout_ms=timeout_ms, seed=1) if run_meta else None
    try:
        compiled = compile_source(
            source,
            grid,
            variables,
            regions,
            z3,
            params,
            loader,
            session=session,
            run_meta=run_meta,
            timeout_ms=timeout_ms,
        )
    except DSLError as exc:
        return SolveResult(STATUS_ERROR, str(exc), error_line=exc.line)
    except Exception as exc:  # defensive: never crash the UI thread
        return SolveResult(STATUS_ERROR, f"internal compile error: {exc}")

    debug = list(compiled.debug)
    witnesses = list(compiled.witnesses)
    if logic and logic != "AUTO":
        try:
            solver = z3.SolverFor(logic)
        except Exception as exc:
            return SolveResult(STATUS_ERROR, f"invalid solver logic {logic!r}: {exc}")
    else:
        solver = z3.Solver()
    if timeout_ms:
        solver.set("timeout", int(timeout_ms))
    for constraint in compiled.constraints:
        solver.add(constraint)

    check = solver.check()
    count = len(compiled.constraints)

    if check == z3.sat:
        model = solver.model()
        values: dict[str, dict[Point, int]] = {}
        kinds: dict[str, PointKind] = {}

        def read(quantities: dict) -> dict[Point, int]:
            out: dict[Point, int] = {}
            for point, z3var in quantities.items():
                # Constant variables store plain Python ints; everything else is
                # a z3 expression evaluated against the model. (cc variables echo
                # their own quantities, which are the region ids.)
                if not z3.is_expr(z3var):
                    out[point] = int(z3var)
                    continue
                evaluated = model.eval(z3var, model_completion=True)
                if z3.is_bool(evaluated) or (z3.is_expr(z3var) and z3.is_bool(z3var)):
                    out[point] = 1 if z3.is_true(evaluated) else 0
                    continue
                try:
                    out[point] = int(evaluated.as_long())
                except Exception:
                    out[point] = 0
            return out

        for variable in compiled.variables:
            values[variable.name] = read(compiled.var_z3[variable.name])
            kinds[variable.name] = variable.kind
        for name, quantities in compiled.derived.items():
            values[name] = read(quantities)
            kinds[name] = compiled.derived_kinds[name]
        return SolveResult(
            STATUS_SAT,
            "Satisfiable — model found.",
            constraint_count=count,
            values=values,
            kinds=kinds,
            debug=debug,
            witnesses=witnesses,
        )

    if check == z3.unsat:
        return SolveResult(
            STATUS_UNSAT,
            "Unsatisfiable — no model exists.",
            constraint_count=count,
            debug=debug,
            witnesses=witnesses,
        )

    return SolveResult(
        STATUS_UNKNOWN,
        "Solver returned unknown.",
        constraint_count=count,
        debug=debug,
        witnesses=witnesses,
    )


def compile_only(
    grid: Grid,
    variables,
    regions,
    source: str,
    params: dict | None = None,
    loader: Callable[[str], str] | None = None,
) -> SolveResult:
    """Compile ``source`` without solving; report constraint count and print()."""

    try:
        import z3
    except Exception:
        return SolveResult(
            STATUS_ERROR,
            "z3 is not installed. Run `pip install z3-solver` to enable compiling.",
        )

    from .compiler import compile_source

    try:
        compiled = compile_source(source, grid, variables, regions, z3, params, loader)
    except DSLError as exc:
        return SolveResult(STATUS_ERROR, str(exc), error_line=exc.line)
    except Exception as exc:  # defensive: never crash the UI thread
        return SolveResult(STATUS_ERROR, f"internal compile error: {exc}")

    count = len(compiled.constraints)
    return SolveResult(
        STATUS_COMPILED,
        f"Compiled successfully — {count} constraint(s) generated.",
        constraint_count=count,
        debug=list(compiled.debug),
    )


def _format_debug(debug: list[str]) -> str:
    """Render the print() debug block (empty string when nothing was printed)."""

    if not debug:
        return ""
    lines = ["", "print():"]
    lines.extend(f"  {line}" for line in debug)
    return "\n".join(lines)


def format_model(result: SolveResult, max_points: int = 200) -> str:
    """Render a solve result as human-readable text for the output pane."""

    if result.status == STATUS_ERROR:
        return f"ERROR: {result.message}{_format_debug(result.debug)}"
    header = f"{result.status.upper()} · {result.constraint_count} constraint(s)"
    if not result.ok:
        return f"{header}\n{result.message}{_format_debug(result.debug)}"

    lines = [header]
    from .values import sort_points

    for name, point_values in result.values.items():
        kind = result.kinds.get(name)
        label = kind.label if kind is not None else "?"
        lines.append(f"\n{name} ({label}):")
        ordered = sort_points(point_values.keys())
        for point in ordered[:max_points]:
            lines.append(f"  {_format_point(point)} = {point_values[point]}")
        if len(ordered) > max_points:
            lines.append(f"  … ({len(ordered) - max_points} more)")
    if result.witnesses:
        lines.append("\nwitnesses:")
        for tag, value in result.witnesses:
            lines.append(f"  {tag} = {value}")
    return "\n".join(lines) + _format_debug(result.debug)


def _format_point(point: Point) -> str:
    if len(point) == 2:
        return f"({point[0]},{point[1]})"
    return f"{point[0]}({point[1]},{point[2]})"
