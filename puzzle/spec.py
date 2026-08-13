"""Puzzle type specifications and puzzle instances.

A **spec** (``impls/<key>.json`` + ``impls/<key>.dsl``) describes one rule:
which solver variables exist, which drawing layers the editor shows and which
DSL program encodes the constraints. It never contains puzzle data.

An **instance** (``impls/samples/<key>.json`` or a payload posted by the UI)
carries the board size, the clue values and the outside-the-board parameters.

Everything here is plain data + JSON (no z3, no UI imports).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .grid import Grid
from .models import Point, PointKind, Region, Variable, VarType, parse_point, point_key

ROOT = Path(__file__).resolve().parent.parent
IMPLS_DIR = ROOT / "impls"
SAMPLES_DIR = IMPLS_DIR / "samples"
LIB_DIR = Path(__file__).resolve().parent / "lib"

# Instance key holding the per-cell region map.
REGION_VAR = "__regions"


@dataclass(frozen=True)
class VarSpec:
    name: str
    kind: PointKind = PointKind.CELL
    var_type: VarType = VarType.NORMAL
    domain: tuple[int, int] | None = None
    doc: str = ""
    # A constant expected to carry a value at *every* point of its lattice
    # (e.g. the printed numbers of Hitori), rather than a sparse clue.
    dense: bool = False

    @classmethod
    def from_json(cls, data: dict) -> "VarSpec":
        domain = data.get("domain")
        return cls(
            name=data["name"],
            kind=PointKind.parse(data.get("kind", "cell")),
            var_type=VarType.parse(data.get("type", "normal")),
            domain=(int(domain[0]), int(domain[1])) if domain else None,
            doc=data.get("doc", ""),
            dense=bool(data.get("dense", False)),
        )

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind.value,
            "type": self.var_type.value,
            "domain": list(self.domain) if self.domain else None,
            "doc": self.doc,
            "dense": self.dense,
        }


@dataclass(frozen=True)
class LayerSpec:
    """One drawable layer: a generic element bound to a variable."""

    id: str
    label: str
    element: str
    target: str = "cell"
    # "input"  -> part of the puzzle statement, edited by the user
    # "output" -> part of the solution, filled in by the solver
    role: str = "input"
    var: str = ""
    # Instance parameter name for outside-the-board layers.
    param: str = ""
    palette: dict[str, str] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict) -> "LayerSpec":
        return cls(
            id=data["id"],
            label=data.get("label", data["id"]),
            element=data["element"],
            target=data.get("target", "cell"),
            role=data.get("role", "input"),
            var=data.get("var", ""),
            param=data.get("param", ""),
            palette=dict(data.get("palette", {})),
            options=dict(data.get("options", {})),
        )

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "element": self.element,
            "target": self.target,
            "role": self.role,
            "var": self.var,
            "param": self.param,
            "palette": self.palette,
            "options": self.options,
        }


@dataclass(frozen=True)
class PuzzleSpec:
    key: str
    en: str
    zh: str
    category: str = ""
    subcategory: str = ""
    rule: str = ""
    aliases: tuple[str, ...] = ()
    default_rows: int = 8
    default_cols: int = 8
    uses_regions: bool = False
    variables: tuple[VarSpec, ...] = ()
    layers: tuple[LayerSpec, ...] = ()
    params: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    notes: str = ""

    @classmethod
    def from_json(cls, data: dict, source: str = "") -> "PuzzleSpec":
        return cls(
            key=data["key"],
            en=data.get("en", data["key"]),
            zh=data.get("zh", ""),
            category=data.get("category", ""),
            subcategory=data.get("subcategory", ""),
            rule=data.get("rule", ""),
            aliases=tuple(data.get("aliases", ())),
            default_rows=int(data.get("defaultRows", 8)),
            default_cols=int(data.get("defaultCols", 8)),
            uses_regions=bool(data.get("usesRegions", False)),
            variables=tuple(VarSpec.from_json(v) for v in data.get("variables", ())),
            layers=tuple(LayerSpec.from_json(v) for v in data.get("layers", ())),
            params=dict(data.get("params", {})),
            source=source or data.get("source", ""),
            notes=data.get("notes", ""),
        )

    def to_json(self, include_source: bool = False) -> dict:
        out = {
            "key": self.key,
            "en": self.en,
            "zh": self.zh,
            "category": self.category,
            "subcategory": self.subcategory,
            "rule": self.rule,
            "aliases": list(self.aliases),
            "defaultRows": self.default_rows,
            "defaultCols": self.default_cols,
            "usesRegions": self.uses_regions,
            "variables": [v.to_json() for v in self.variables],
            "layers": [layer.to_json() for layer in self.layers],
            "params": self.params,
            "notes": self.notes,
        }
        if include_source:
            out["source"] = self.source
        return out

    def var_spec(self, name: str) -> VarSpec | None:
        for var in self.variables:
            if var.name == name:
                return var
        return None


@dataclass
class Instance:
    """Concrete puzzle data: board size, clues, regions and outside clues."""

    puzzle: str
    rows: int
    cols: int
    # variable name -> {point key -> integer value}
    clues: dict[str, dict[str, int]] = field(default_factory=dict)
    # per-cell region id ("r,c" -> id)
    regions: dict[str, int] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    title: str = ""

    @classmethod
    def from_json(cls, data: dict) -> "Instance":
        return cls(
            puzzle=data["puzzle"],
            rows=int(data["rows"]),
            cols=int(data["cols"]),
            clues={k: dict(v) for k, v in data.get("clues", {}).items()},
            regions=dict(data.get("regions", {})),
            params=dict(data.get("params", {})),
            title=data.get("title", ""),
        )

    def to_json(self) -> dict:
        return {
            "puzzle": self.puzzle,
            "rows": self.rows,
            "cols": self.cols,
            "clues": self.clues,
            "regions": self.regions,
            "params": self.params,
            "title": self.title,
        }


def build_grid(instance: Instance) -> Grid:
    return Grid(instance.rows, instance.cols)


def build_variables(spec: PuzzleSpec, instance: Instance, grid: Grid) -> list[Variable]:
    """Materialise the spec's variables, injecting the instance's clue values."""

    out: list[Variable] = []
    for var_spec in spec.variables:
        givens: dict[Point, int] = {}
        for raw, value in instance.clues.get(var_spec.name, {}).items():
            if value is None:
                continue
            point = parse_point(raw, var_spec.kind)
            if grid.contains(var_spec.kind, point):
                givens[point] = int(value)
        out.append(Variable(var_spec.name, var_spec.kind, var_spec.var_type, var_spec.domain, givens))
    return out


def build_regions(spec: PuzzleSpec, instance: Instance, grid: Grid) -> list[Region]:
    """Group cells by their instance region id (ordered by id)."""

    if not instance.regions:
        return []
    buckets: dict[int, list[Point]] = {}
    for raw, rid in instance.regions.items():
        if rid is None:
            continue
        point = parse_point(raw, PointKind.CELL)
        if grid.contains(PointKind.CELL, point):
            buckets.setdefault(int(rid), []).append(point)
    return [
        Region(f"r{rid}", PointKind.CELL, tuple(sorted(points)))
        for rid, points in sorted(buckets.items())
    ]


def build_params(spec: PuzzleSpec, instance: Instance) -> dict[str, Any]:
    params = dict(spec.params.get("defaults", {})) if spec.params else {}
    params.update(instance.params)
    params.setdefault("rows", instance.rows)
    params.setdefault("cols", instance.cols)
    return params


# -- loading ------------------------------------------------------------------


def make_loader(extra_dirs: tuple[Path, ...] = ()) -> Any:
    """A DSL ``import`` resolver searching the shared lib then ``impls/``."""

    search = (LIB_DIR, IMPLS_DIR, *extra_dirs)

    def load(name: str) -> str:
        rel = name if name.endswith(".dsl") else f"{name}.dsl"
        for base in search:
            candidate = (base / rel).resolve()
            if candidate.is_file() and base.resolve() in candidate.parents:
                return candidate.read_text(encoding="utf-8")
        raise FileNotFoundError(f"module {name!r} not found in {[str(p) for p in search]}")

    return load


def load_spec(key: str) -> PuzzleSpec:
    meta_path = IMPLS_DIR / f"{key}.json"
    if not meta_path.is_file():
        raise FileNotFoundError(f"no implementation for puzzle {key!r}")
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    dsl_path = IMPLS_DIR / f"{key}.dsl"
    source = dsl_path.read_text(encoding="utf-8") if dsl_path.is_file() else data.get("source", "")
    return PuzzleSpec.from_json(data, source)


def implemented_keys() -> list[str]:
    if not IMPLS_DIR.is_dir():
        return []
    return sorted(p.stem for p in IMPLS_DIR.glob("*.json"))


def load_sample(key: str) -> Instance | None:
    path = SAMPLES_DIR / f"{key}.json"
    if not path.is_file():
        return None
    return Instance.from_json(json.loads(path.read_text(encoding="utf-8")))


def region_map_from_regions(regions: list[Region]) -> dict[str, int]:
    """Inverse of :func:`build_regions` (used when exporting an instance)."""

    out: dict[str, int] = {}
    for index, region in enumerate(regions):
        for point in region.points:
            out[point_key(point)] = index
    return out
