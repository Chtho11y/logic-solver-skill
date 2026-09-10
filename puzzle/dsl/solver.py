"""Compile and solve a puzzle DSL program through cspuz.

This is the single entry point the UI calls. cspuz owns the constraint model;
the concrete solver (cspuz_core, Z3, csugar or Sugar) is selected at runtime.

UI-independent (no PyQt import).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..backends import (
    BACKEND_NAMES,
    BackendError,
    BackendTimeoutError,
    BackendUnknownError,
    backend_configuration,
    cspuz_available,
    list_backends,
    normalize_backend,
    resolve_backend,
)
from ..grid import Grid
from ..models import Point, PointKind
from .errors import DSLError

# Result status strings.
STATUS_SAT = "sat"
STATUS_UNSAT = "unsat"
STATUS_UNKNOWN = "unknown"
STATUS_ERROR = "error"
STATUS_COMPILED = "compiled"

# Concrete solvers offered by cspuz. ``SOLVER_LOGICS`` remains as a deprecated
# import alias for clients built against the old Z3-only API.
SOLVER_BACKENDS: tuple[str, ...] = BACKEND_NAMES
SOLVER_LOGICS: tuple[str, ...] = SOLVER_BACKENDS


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
    backend: str = ""

    @property
    def ok(self) -> bool:
        return self.status == STATUS_SAT


def is_available() -> bool:
    """Whether cspuz and at least one concrete backend are available."""

    return cspuz_available() and any(
        info.available for info in list_backends() if info.name != "auto"
    )


def backend_status() -> list[dict[str, Any]]:
    """JSON-friendly runtime status for every selectable backend."""

    return [info.to_json() for info in list_backends()]


def _select_backend(backend: str | None, logic: str | None) -> str:
    if backend is not None:
        return normalize_backend(backend)
    if logic is None or str(logic).strip().lower() in ("", "auto"):
        return "auto"
    normalized = str(logic).strip().lower()
    if normalized in SOLVER_BACKENDS:
        return normalize_backend(normalized)
    raise BackendError(
        f"Z3 logic {logic!r} is no longer a backend selector; "
        f"use backend='z3' or one of {', '.join(SOLVER_BACKENDS)}"
    )


def solve(
    grid: Grid,
    variables,
    regions,
    source: str,
    logic: str | None = "AUTO",
    params: dict | None = None,
    loader: Callable[[str], str] | None = None,
    timeout_ms: int | None = None,
    *,
    backend: str | None = None,
) -> SolveResult:
    """Compile ``source`` and solve it; return a structured result.

    ``backend`` selects a cspuz concrete solver. The old ``logic="AUTO"``
    argument remains accepted as an alias for ``backend="auto"``.
    """

    if not cspuz_available():
        return SolveResult(
            STATUS_ERROR,
            "cspuz is not installed. Run `pip install -r requirements.txt`.",
        )

    from .compiler import compile_source

    compiled = None
    resolved = ""
    try:
        selected = _select_backend(backend, logic)
        with backend_configuration(selected, timeout_ms) as resolved:
            compiled = compile_source(
                source,
                grid,
                variables,
                regions,
                params=params,
                loader=loader,
            )
            compiled.model.add_constraints(compiled.constraints)
            satisfiable = compiled.model.find_answer(resolved, timeout_ms)
    except DSLError as exc:
        return SolveResult(STATUS_ERROR, str(exc), error_line=exc.line)
    except BackendTimeoutError as exc:
        return SolveResult(
            STATUS_UNKNOWN,
            str(exc),
            constraint_count=len(compiled.constraints) if compiled else 0,
            debug=list(compiled.debug) if compiled else [],
            backend=resolved,
        )
    except BackendUnknownError as exc:
        return SolveResult(
            STATUS_UNKNOWN,
            str(exc),
            constraint_count=len(compiled.constraints) if compiled else 0,
            debug=list(compiled.debug) if compiled else [],
            backend=resolved,
        )
    except BackendError as exc:
        return SolveResult(STATUS_ERROR, str(exc), backend=resolved)
    except Exception as exc:  # defensive: never crash the UI thread
        phase = "solve" if compiled is not None else "compile"
        return SolveResult(
            STATUS_ERROR,
            f"internal {phase} error: {exc}",
            constraint_count=len(compiled.constraints) if compiled else 0,
            debug=list(compiled.debug) if compiled else [],
            backend=resolved,
        )

    debug = list(compiled.debug)
    count = len(compiled.constraints)

    if satisfiable:
        values: dict[str, dict[Point, int]] = {}
        kinds: dict[str, PointKind] = {}
        missing: list[str] = []

        def read(name: str, quantities: dict) -> dict[Point, int]:
            out: dict[Point, int] = {}
            for point, term in quantities.items():
                value = compiled.model.value(term)
                if value is None:
                    missing.append(f"{name}[{point}]")
                else:
                    out[point] = int(value)
            return out

        for variable in compiled.variables:
            values[variable.name] = read(
                variable.name, compiled.var_terms[variable.name]
            )
            kinds[variable.name] = variable.kind
        for name, quantities in compiled.derived.items():
            values[name] = read(name, quantities)
            kinds[name] = compiled.derived_kinds[name]
        if missing:
            shown = ", ".join(missing[:3])
            suffix = " …" if len(missing) > 3 else ""
            return SolveResult(
                STATUS_UNKNOWN,
                f"{resolved} returned an incomplete model: {shown}{suffix}",
                constraint_count=count,
                debug=debug,
                backend=resolved,
            )
        return SolveResult(
            STATUS_SAT,
            f"Satisfiable — model found with {resolved}.",
            constraint_count=count,
            values=values,
            kinds=kinds,
            debug=debug,
            backend=resolved,
        )

    return SolveResult(
        STATUS_UNSAT,
        f"Unsatisfiable — no model exists ({resolved}).",
        constraint_count=count,
        debug=debug,
        backend=resolved,
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

    if not cspuz_available():
        return SolveResult(
            STATUS_ERROR,
            "cspuz is not installed. Run `pip install -r requirements.txt`.",
        )

    from .compiler import compile_source

    try:
        compiled = compile_source(
            source,
            grid,
            variables,
            regions,
            params=params,
            loader=loader,
        )
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
    return "\n".join(lines) + _format_debug(result.debug)


def _format_point(point: Point) -> str:
    if len(point) == 2:
        return f"({point[0]},{point[1]})"
    return f"{point[0]}({point[1]},{point[2]})"
