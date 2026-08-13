"""Scaffolding helpers for puzzle implementations.

Every rule is implemented by three files under ``impls/``:

* ``<key>.json``          -- the spec: variables + drawing layers
* ``<key>.dsl``           -- the constraints
* ``samples/<key>.json``  -- a sample instance

The :func:`layer` presets below keep the specs consistent: layers are described
purely in terms of the generic elements from :mod:`puzzle.elements`, so no
front-end code ever needs to know which puzzle it is drawing.

Usage::

    python -m tools.scaffold new <key>            # create stub files
    python -m tools.scaffold list                 # implemented puzzles
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from puzzle.registry import get_rule  # noqa: E402
from puzzle.spec import IMPLS_DIR, SAMPLES_DIR  # noqa: E402

# -- layer presets ------------------------------------------------------------

BLACK = "#232733"
WHITE = "#ffffff"


def layer(
    id: str,
    label: str,
    element: str,
    *,
    target: str = "cell",
    role: str = "input",
    var: str = "",
    param: str = "",
    palette: dict | None = None,
    **options: Any,
) -> dict:
    out = {
        "id": id,
        "label": label,
        "element": element,
        "target": target,
        "role": role,
    }
    if var:
        out["var"] = var
    if param:
        out["param"] = param
    if palette:
        out["palette"] = palette
    if options:
        out["options"] = options
    return out


def shade(var: str = "x", label: str = "涂黑", *, role: str = "output", **kw) -> dict:
    return layer(
        "shade", label, "shade", role=role, var=var,
        palette={"1": BLACK, "2": "#7f8ea3"}, **kw,
    )


def clue_number(var: str = "n", label: str = "数字提示", **kw) -> dict:
    return layer("clue", label, "number", role="input", var=var, min=0, **kw)


def answer_number(var: str = "x", label: str = "填数", **kw) -> dict:
    return layer("answer", label, "number", role="output", var=var,
                 palette={"*": "#1565c0"}, **kw)


def clue_circle(var: str = "o", label: str = "圆圈", **kw) -> dict:
    return layer(
        "circle", label, "circle", role="input", var=var,
        palette={"1": WHITE, "2": BLACK, "3": "#9aa4b2"}, **kw,
    )


def clue_arrow(var: str = "d", label: str = "箭头", **kw) -> dict:
    return layer("arrow", label, "arrow", role="input", var=var, **kw)


def region_layer(label: str = "区域划分") -> dict:
    return layer("regions", label, "region", role="input", var="__regions")


def partition_layer(var: str = "c", label: str = "分区结果") -> dict:
    return layer("partition", label, "region", role="output", var=var)


def link_layer(var: str = "e", label: str = "回路", **kw) -> dict:
    return layer("loop", label, "link", target="edge", role="output", var=var, **kw)


def edgeline_layer(var: str = "e", label: str = "边界线", *, role: str = "output", **kw) -> dict:
    return layer("edges", label, "edgeline", target="edge", role=role, var=var, **kw)


def outside_layer(
    id: str = "outside",
    label: str = "盘外提示",
    *,
    param: str = "outside",
    sides: tuple[str, ...] = ("top", "left"),
    mode: str = "int",
) -> dict:
    return layer(
        id, label, "outside", target="outside", role="input", param=param,
        sides=list(sides), mode=mode,
    )


def var(
    name: str,
    kind: str = "cell",
    type: str = "normal",
    domain=None,
    doc: str = "",
    dense: bool = False,
) -> dict:
    out: dict[str, Any] = {"name": name, "kind": kind, "type": type}
    if domain is not None:
        out["domain"] = list(domain)
    if doc:
        out["doc"] = doc
    if dense:
        out["dense"] = True
    return out


SHADE_VAR = var("x", "cell", "normal", (0, 1), "0 = 留白, 1 = 涂黑")
LOOP_VAR = var("e", "edge", "normal", (0, 1), "1 = 回路")
CLUE_VAR = var("n", "cell", "constant", None, "题目给出的数字提示")


def write_spec(
    key: str,
    *,
    variables: list[dict],
    layers: list[dict],
    rows: int = 8,
    cols: int = 8,
    uses_regions: bool = False,
    notes: str = "",
    params: dict | None = None,
    unencoded: list[str] | None = None,
) -> Path:
    """Write ``impls/<key>.json``, filling names/rule text from ``rules.txt``."""

    entry = get_rule(key)
    data = {
        "key": key,
        "en": entry.en if entry else key,
        "zh": entry.zh if entry else "",
        "category": entry.category if entry else "",
        "subcategory": entry.subcategory if entry else "",
        "rule": entry.rule if entry else "",
        "defaultRows": rows,
        "defaultCols": cols,
        "usesRegions": uses_regions,
        "variables": variables,
        "layers": layers,
        "params": params or {},
        "notes": notes,
    }
    if unencoded:
        data["unencodedClues"] = list(unencoded)
    IMPLS_DIR.mkdir(parents=True, exist_ok=True)
    path = IMPLS_DIR / f"{key}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_sample(key: str, instance: dict) -> Path:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    path = SAMPLES_DIR / f"{key}.json"
    path.write_text(json.dumps(instance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def sample(key: str, rows: int, cols: int, **kw) -> dict:
    return {"puzzle": key, "rows": rows, "cols": cols, **kw}


# -- CLI ----------------------------------------------------------------------


def _cmd_new(args: argparse.Namespace) -> int:
    key = args.key
    entry = get_rule(key)
    if entry is None:
        print(f"warning: {key!r} is not listed in rules.txt", file=sys.stderr)
    spec_path = IMPLS_DIR / f"{key}.json"
    if spec_path.exists() and not args.force:
        print(f"{spec_path} already exists (use --force)", file=sys.stderr)
        return 1
    write_spec(
        key,
        variables=[SHADE_VAR, CLUE_VAR],
        layers=[clue_number(), shade()],
        rows=args.rows,
        cols=args.cols,
    )
    dsl_path = IMPLS_DIR / f"{key}.dsl"
    if not dsl_path.exists() or args.force:
        rule = entry.rule if entry else ""
        dsl_path.write_text(
            f"# {key} — {entry.zh if entry else key}\n# {rule}\n\nimport \"shading\"\n\n",
            encoding="utf-8",
        )
    write_sample(key, sample(key, args.rows, args.cols, clues={"n": {}}))
    print(f"created {spec_path}, {dsl_path} and the sample instance")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    for path in sorted(IMPLS_DIR.glob("*.json")):
        entry = get_rule(path.stem)
        print(f"{path.stem:16} {entry.zh if entry else '':10} {entry.en if entry else ''}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="scaffold puzzle implementations")
    sub = parser.add_subparsers(dest="cmd", required=True)
    new = sub.add_parser("new", help="create stub files for a rule")
    new.add_argument("key")
    new.add_argument("--rows", type=int, default=8)
    new.add_argument("--cols", type=int, default=8)
    new.add_argument("--force", action="store_true")
    new.set_defaults(func=_cmd_new)
    listing = sub.add_parser("list", help="list implemented puzzles")
    listing.set_defaults(func=_cmd_list)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
