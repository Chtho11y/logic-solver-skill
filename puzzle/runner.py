"""Turn a (spec, instance) pair into a solved board.

This is the bridge between the JSON world (front-end, samples, agent tools) and
the DSL solver: it builds the grid/variables/regions, runs z3 and echoes every
variable back as a JSON-friendly ``{layer: {point: value}}`` map.
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


def solve_instance(
    spec: PuzzleSpec,
    instance: Instance,
    logic: str = "AUTO",
    timeout_ms: int | None = 60000,
    source: str | None = None,
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
        params=params,
        loader=make_loader(),
        timeout_ms=timeout_ms,
    )
    payload: dict[str, Any] = {
        "status": result.status,
        "message": result.message,
        "constraints": result.constraint_count,
        "debug": result.debug,
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
    """Solve a raw ``{"instance": {...}}`` request coming from the UI.

    Optional ``spec`` lets a custom / mixed rule run without an ``impls/`` file.
    Optional ``source`` overrides the DSL (in-app editor, or a one-off program).
    """

    instance = Instance.from_json(payload["instance"])
    raw_spec = payload.get("spec")
    if isinstance(raw_spec, dict):
        spec = PuzzleSpec.from_json(raw_spec, source=payload.get("source") or "")
    else:
        spec = load_spec(instance.puzzle)
    return solve_instance(
        spec,
        instance,
        logic=payload.get("logic", "AUTO"),
        timeout_ms=payload.get("timeoutMs", 60000),
        source=payload.get("source"),
    )
