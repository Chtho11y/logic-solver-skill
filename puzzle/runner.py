"""Turn a (spec, instance) pair into a solved board.

This is the bridge between the JSON world (front-end, samples, agent tools) and
the DSL solver: it builds the grid/variables/regions, runs the selected cspuz
backend and echoes every variable as ``{layer: {point: value}}``.
"""

from __future__ import annotations

from typing import Any

from .dsl import STATUS_SAT, solve
from .models import point_key
from .spec import (
    Instance,
    PuzzleSpec,
    build_grid,
    build_params,
    build_regions,
    build_variables,
    load_spec,
    make_loader,
)

DEFAULT_TIMEOUT_MS = 60000


def solve_instance(
    spec: PuzzleSpec,
    instance: Instance,
    backend: str = "auto",
    timeout_ms: int | None = DEFAULT_TIMEOUT_MS,
    source: str | None = None,
    *,
    logic: str | None = None,
) -> dict[str, Any]:
    """Solve one puzzle instance and return a JSON-serialisable result."""

    grid = build_grid(instance)
    variables = build_variables(spec, instance, grid)
    regions = build_regions(spec, instance, grid)
    params = build_params(spec, instance)
    program = spec.source if source is None else source
    if not program.strip():
        return {"status": "error", "message": f"puzzle {spec.key!r} has no DSL program"}

    result = solve(
        grid,
        variables,
        regions,
        program,
        logic=logic,
        backend=backend if logic is None else None,
        params=params,
        loader=make_loader(),
        timeout_ms=timeout_ms,
    )
    payload: dict[str, Any] = {
        "status": result.status,
        "message": result.message,
        "constraints": result.constraint_count,
        "debug": result.debug,
        "backend": result.backend,
    }
    if result.error_line is not None:
        payload["errorLine"] = result.error_line
    if result.status == STATUS_SAT:
        payload["values"] = {
            name: {point_key(point): value for point, value in points.items()}
            for name, points in result.values.items()
        }
        payload["kinds"] = {name: kind.value for name, kind in result.kinds.items()}
    return payload


def solve_payload(payload: dict) -> dict[str, Any]:
    """Solve a raw ``{"instance": {...}}`` request coming from the UI."""

    instance = Instance.from_json(payload["instance"])
    spec = load_spec(instance.puzzle)
    requested_backend = payload.get("backend")
    return solve_instance(
        spec,
        instance,
        backend=requested_backend or "auto",
        timeout_ms=payload.get("timeoutMs", DEFAULT_TIMEOUT_MS),
        source=payload.get("source"),
        # The new backend field takes precedence over deprecated logic.
        logic=None if requested_backend is not None else payload.get("logic"),
    )
