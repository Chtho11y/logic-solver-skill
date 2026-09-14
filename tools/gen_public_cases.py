"""Decode public puzz.link examples and write unique-solution fixtures.

    python -m tools.gen_public_cases

Requires Node.js and the ``pzpr`` npm package (installed on demand next to
``puzzle/importing/pzpr_dump.js``).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from puzzle.importing import PuzzleImportError, import_url  # noqa: E402
from puzzle.runner import solve_instance  # noqa: E402
from puzzle.spec import Instance, load_spec  # noqa: E402

# Official pzprjs ``test/script/<pid>.js`` example URLs (the `url:` field).
# These are the engine's own typical boards, not hand-drawn SAT probes.
PUBLIC: list[tuple[str, str, str]] = [
    ("nurikabe", "pzprjs example 5x5", "https://puzz.link/p?nurikabe/5/5/g5k2o1k3g"),
    ("slither", "pzprjs example 5x5", "https://puzz.link/p?slither/5/5/cbcbcddad"),
    ("masyu", "pzprjs example 6x6", "https://puzz.link/p?mashu/6/6/1063000i3000"),
    ("heyawake", "pzprjs example 6x6", "https://puzz.link/p?heyawake/6/6/lll155007rs12222j"),
    ("yajilin", "pzprjs example 5x5", "https://puzz.link/p?yajilin/5/5/m32j10"),
    ("shikaku", "pzprjs example 6x6", "https://puzz.link/p?shikaku/6/6/j3g56h6t6h23g5j"),
    ("skyscrapers", "puzz.link example 5x5", "https://puzz.link/p?skyscrapers/5/5/g2l2g43l35"),
    ("akari", "pzprjs example 6x6", "https://puzz.link/p?akari/6/6/nekcakbl"),
    ("hitori", "pzprjs example 4x4", "https://puzz.link/p?hitori/4/4/1114142333214213"),
    ("norinori", "pzprjs example 5x5", "https://puzz.link/p?norinori/5/5/cag4ocjo"),
    ("kurodoko", "pzprjs example 5x5", "https://puzz.link/p?kurodoko/5/5/i7g5l2l2g4i"),
]

OUT = ROOT / "tests" / "cases" / "public"


def _grid(values: dict[str, int], rows: int, cols: int, *, binary: bool) -> list[str]:
    lines = []
    for row in range(rows):
        cells = []
        for col in range(cols):
            value = values.get(f"{row},{col}")
            if value is None:
                cells.append(".")
            elif binary:
                cells.append("#" if value else ".")
            else:
                cells.append(str(value))
        lines.append(" ".join(cells) if not binary else "".join(cells))
    return lines


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for key, name, url in PUBLIC:
        print(f"-- {key} {url}")
        try:
            payload = import_url(url)
        except PuzzleImportError as exc:
            print(f"   skip import: {exc}")
            continue
        instance = payload.get("instance")
        if not instance:
            print(f"   skip: no instance ({payload.get('warnings')})")
            continue
        spec = load_spec(key)
        inst = Instance.from_json(instance)
        result = solve_instance(spec, inst, timeout_ms=120000)
        status = result.get("status")
        print(f"   {status}  layers={ [l['id'] for l in payload['layers']] }")
        if status != "sat":
            print(f"   skip solve: {result.get('message', '')[:160]}")
            continue
        values = result.get("values") or {}
        answer = {}
        for layer in spec.layers:
            if layer.role != "output" or not layer.var:
                continue
            got = values.get(layer.var) or {}
            binary = layer.element in {"shade", "edgeline", "link", "star", "bulb"}
            if layer.target == "edge":
                answer[layer.var] = dict(got)
            else:
                answer[layer.var] = _grid(got, inst.rows, inst.cols, binary=binary)
        case = {
            "puzzle": key,
            "timeoutMs": 120000,
            "cases": [
                {
                    "name": name,
                    "source_url": url,
                    "unique": True,
                    "rows": inst.rows,
                    "cols": inst.cols,
                    "clues": instance.get("clues") or {},
                    "regions": instance.get("regions") or {},
                    "params": instance.get("params") or {},
                    "answer": answer,
                }
            ],
        }
        path = OUT / f"{key}.json"
        path.write_text(json.dumps(case, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"   wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
