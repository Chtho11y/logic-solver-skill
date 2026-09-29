"""Turn a (spec, instance) pair into a solved board.

This is the bridge between the JSON world (front-end, samples, agent tools) and
the DSL solver: it builds the grid/variables/regions, runs the selected cspuz
backend and echoes every variable as ``{layer: {point: value}}``.
"""

from __future__ import annotations

from typing import Any
from dataclasses import replace
import re

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
        "partial": spec.partial,
        "ruleNotes": spec.notes,
        "unencodedClues": list(spec.unencoded_clues),
        "sourceModified": source is not None and source != spec.source,
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
    drawing_constraints = []
    if payload.get("spec") is not None:
        spec = PuzzleSpec.from_json(payload["spec"], source=payload["spec"].get("source") or "")
        names = [variable.name for variable in spec.variables]
        if len(names) != len(set(names)) or any(name.startswith("__") or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name) for name in names):
            raise ValueError("Variable names must be unique identifiers")
        if any(v.domain and v.domain[0] > v.domain[1] for v in spec.variables):
            raise ValueError("Variable domain minimum exceeds maximum")
        if any(layer.var and layer.var not in names and layer.var != "__regions" for layer in spec.layers):
            raise ValueError("Layer refers to an unknown variable")
    else:
        spec = load_spec(instance.puzzle)
    if "documents" in payload:
        from .importing.penpa import decode_penpa
        from .importing.bind import bind_instance
        instance.clues = {}
        instance.regions = {}
        seen = set()
        for document in payload["documents"]:
            name = document["id"]
            if name in seen:
                raise ValueError("Duplicate variable document")
            seen.add(name)
            if name not in {"__outside", "__regions", "__unbound", *[v.name for v in spec.variables]}:
                raise ValueError(f"Unknown variable document: {name}")
            board = decode_penpa(document["url"])
            if (board.rows, board.cols) != (instance.rows, instance.cols):
                raise ValueError("Variable boards must have the same dimensions")
            if board.warnings:
                raise ValueError("Unsupported drawing: " + "; ".join(board.warnings))
            layers = tuple(layer for layer in spec.layers if layer.role == "input" and (
                layer.var == name or (name == "__outside" and layer.target == "outside")))
            if name == "__regions":
                instance.regions = board.regions or {f"{r},{c}": 0 for r in range(board.rows) for c in range(board.cols)}
                continue
            if name == "__unbound":
                if board.cells or board.edges or board.outside:
                    raise ValueError("存在未绑定的绘制内容，请先选择变量归属")
                continue
            variable = spec.var_spec(name)
            if variable and variable.var_type.value == "cc":
                for key, mark in board.edges.items():
                    if mark.line:
                        direction, row, col = key.split(",")
                        drawing_constraints.append(f'{name}.border[edge("{direction}", {int(row)}, {int(col)})] == 1')
                continue
            bound = bind_instance(board, replace(spec, layers=layers, uses_regions=False))
            if bound["_warnings"]:
                raise ValueError("; ".join(bound["_warnings"]))
            for variable, clues in bound["clues"].items():
                instance.clues.setdefault(variable, {}).update(clues)
            if name == "__outside":
                for side in ("top", "bottom", "left", "right"):
                    if side in bound["params"]:
                        instance.params[side] = bound["params"][side]
    requested_backend = payload.get("backend")
    source = payload.get("source")
    if drawing_constraints:
        source = spec.source if source is None else source
        if source.strip():
            source += "\n" + "\n".join(drawing_constraints)
    return solve_instance(
        spec,
        instance,
        backend=requested_backend or "auto",
        timeout_ms=payload.get("timeoutMs", DEFAULT_TIMEOUT_MS),
        source=source,
        # The new backend field takes precedence over deprecated logic.
        logic=None if requested_backend is not None else payload.get("logic"),
    )
