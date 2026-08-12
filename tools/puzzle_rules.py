"""``puzzle-rules`` — the agent-facing tool for the puzzle rule catalogue.

It answers the two directions the skill needs:

* **name -> rule**: ``find`` resolves a key / English / Chinese name (or a fuzzy
  variant) to the exact rule text, its category and its implementation status.
* **rule -> name**: ``identify`` takes a rule description and ranks which
  puzzles it matches.

Plus the plumbing needed to implement a new rule quickly:

* ``show``     — everything known about one rule (spec, DSL, sample, layers)
* ``lib``      — the shared DSL templates and their helper signatures
* ``builtins`` — the DSL builtin/constant reference
* ``elements`` — the generic drawing elements available to layers
* ``todo``     — rules that still have no implementation

Every command accepts ``--json`` for machine-readable output.

    python -m tools.puzzle_rules find 数墙
    python -m tools.puzzle_rules identify "涂黑一些格子使留白连通" --json
    python -m tools.puzzle_rules show nurikabe
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from puzzle.dsl import function_table  # noqa: E402
from puzzle.elements import ELEMENT_TYPES  # noqa: E402
from puzzle.registry import (  # noqa: E402
    RuleEntry,
    catalogue,
    categories,
    get_rule,
    impl_paths,
    load_rules,
    missing_keys,
    search_by_description,
    search_rules,
)
from puzzle.spec import LIB_DIR, implemented_keys, load_sample, load_spec  # noqa: E402


def _emit(data, as_json: bool, text: str = "") -> int:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(text)
    return 0


def _entry_line(entry: RuleEntry, score: float | None = None) -> str:
    mark = "✓" if entry.implemented else " "
    head = f"{mark} {entry.key:14} {entry.zh or '-':10} {entry.en}"
    if score is not None:
        head = f"{head}  ({score:.0f})"
    return f"{head}\n    [{entry.category} / {entry.subcategory or '-'}] {entry.rule}"


# -- commands -----------------------------------------------------------------


def cmd_find(args) -> int:
    hits = search_rules(args.query, args.limit)
    data = [entry.to_json() | {"score": round(score, 2)} for entry, score in hits]
    if not hits:
        return _emit([], args.json, f"no rule matches {args.query!r}")
    text = "\n".join(_entry_line(entry, score) for entry, score in hits)
    return _emit(data, args.json, text)


def cmd_identify(args) -> int:
    text = " ".join(args.text)
    hits = search_by_description(text, args.limit)
    if not hits:
        hits = search_rules(text, args.limit)
    data = [entry.to_json() | {"score": round(score, 2)} for entry, score in hits]
    rendered = "\n".join(_entry_line(entry, score) for entry, score in hits)
    return _emit(data, args.json, rendered or "no candidate found")


def cmd_show(args) -> int:
    entry = get_rule(args.key)
    if entry is None:
        return _emit({"error": "unknown rule"}, args.json, f"unknown rule {args.key!r}")
    paths = impl_paths(args.key)
    data: dict = {"rule": entry.to_json(), "implemented": entry.implemented}
    lines = [_entry_line(entry)]
    if entry.implemented:
        spec = load_spec(args.key)
        instance = load_sample(args.key)
        data["spec"] = spec.to_json(include_source=True)
        data["sample"] = instance.to_json() if instance else None
        data["paths"] = {name: str(path) for name, path in paths.items()}
        lines.append(f"\n板面默认 {spec.default_rows}x{spec.default_cols}"
                     f"  区域: {'是' if spec.uses_regions else '否'}")
        lines.append("变量:")
        for var in spec.variables:
            domain = f" domain={list(var.domain)}" if var.domain else ""
            lines.append(f"  {var.name:4} {var.kind.value:6} {var.var_type.value:8}{domain}  {var.doc}")
        lines.append("图层:")
        for layer in spec.layers:
            lines.append(
                f"  {layer.id:10} {layer.element:9} {layer.target:7} {layer.role:6} "
                f"var={layer.var or layer.param}  {layer.label}"
            )
        if spec.notes:
            lines.append(f"备注: {spec.notes}")
        lines.append(f"\n--- {paths['dsl'].name} ---\n{spec.source}")
    else:
        lines.append("\n尚未实现。使用 `python -m tools.scaffold new "
                     f"{args.key}` 创建 spec/dsl/sample 骨架。")
    return _emit(data, args.json, "\n".join(lines))


def cmd_list(args) -> int:
    entries = load_rules()
    if args.category:
        entries = tuple(e for e in entries if args.category in (e.category, e.subcategory))
    if args.implemented:
        entries = tuple(e for e in entries if e.implemented)
    data = [entry.to_json() for entry in entries]
    text = "\n".join(
        f"{'✓' if e.implemented else ' '} {e.key:14} {e.zh or '-':10} {e.en:26} {e.category}"
        for e in entries
    )
    return _emit(data, args.json, text + f"\n\n{len(entries)} rule(s)")


def cmd_categories(args) -> int:
    groups = categories()
    data = {
        name: {
            "total": len(items),
            "implemented": sum(1 for i in items if i.implemented),
            "keys": [i.key for i in items],
        }
        for name, items in groups.items()
    }
    text = "\n".join(
        f"{name:10} {info['implemented']:3}/{info['total']:<3} implemented"
        for name, info in data.items()
    )
    return _emit(data, args.json, text)


def cmd_todo(args) -> int:
    keys = missing_keys()
    data = [get_rule(k).to_json() for k in keys]
    text = "\n".join(f"{k:14} {get_rule(k).zh}" for k in keys)
    return _emit(data, args.json, text + f"\n\n{len(keys)} rule(s) without a solver")


def cmd_lib(args) -> int:
    modules = {}
    lines = []
    for path in sorted(LIB_DIR.glob("*.dsl")):
        source = path.read_text(encoding="utf-8")
        helpers = [
            line.strip()[4:].split(":")[0]
            for line in source.splitlines()
            if line.startswith("def ")
        ]
        modules[path.stem] = {"helpers": helpers, "source": source if args.full else ""}
        lines.append(f"{path.stem}\n  " + "\n  ".join(helpers))
    return _emit(modules, args.json, "\n\n".join(lines))


def cmd_builtins(args) -> int:
    entries = [entry.__dict__ for entry in function_table()]
    text = "\n".join(
        f"{e['category']:12} {e['signature']:34} {e['doc']}" for e in entries
    )
    return _emit(entries, args.json, text)


def cmd_elements(args) -> int:
    data = [
        {
            "id": e.id,
            "label": e.label,
            "targets": list(e.targets),
            "editor": e.editor,
            "doc": e.doc,
            "values": e.values,
        }
        for e in ELEMENT_TYPES
    ]
    text = "\n".join(
        f"{e['id']:10} {e['label']:8} {'/'.join(e['targets']):22} {e['doc']}" for e in data
    )
    return _emit(data, args.json, text)


def cmd_status(args) -> int:
    rules = catalogue()
    done = implemented_keys()
    data = {
        "rules": len(rules),
        "implemented": len(done),
        "keys": done,
    }
    return _emit(
        data, args.json, f"{len(done)}/{len(rules)} rules implemented\n" + " ".join(done)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="puzzle-rules", description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("find", help="name (any language) -> rule")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=8)
    p.set_defaults(func=cmd_find)

    p = sub.add_parser("identify", help="rule description -> candidate puzzles")
    p.add_argument("text", nargs="+")
    p.add_argument("--limit", type=int, default=8)
    p.set_defaults(func=cmd_identify)

    p = sub.add_parser("show", help="everything about one rule")
    p.add_argument("key")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("list", help="list rules")
    p.add_argument("--category")
    p.add_argument("--implemented", action="store_true")
    p.set_defaults(func=cmd_list)

    sub.add_parser("categories", help="per-category coverage").set_defaults(func=cmd_categories)
    sub.add_parser("todo", help="rules without a solver").set_defaults(func=cmd_todo)
    sub.add_parser("builtins", help="DSL builtin reference").set_defaults(func=cmd_builtins)
    sub.add_parser("elements", help="generic drawing elements").set_defaults(func=cmd_elements)
    sub.add_parser("status", help="implementation coverage").set_defaults(func=cmd_status)

    p = sub.add_parser("lib", help="shared DSL templates")
    p.add_argument("--full", action="store_true", help="include the module sources")
    p.set_defaults(func=cmd_lib)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
