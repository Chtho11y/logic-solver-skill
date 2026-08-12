"""Redo generator: authors impls/ from rules.txt metadata + per-puzzle DSL.

Metadata (en/zh/rule/category/subcategory) is ALWAYS read from rules.txt so it
can never drift from the catalogue. Only the DSL body and the layer/variable
shape are authored here, one puzzle at a time.

    python gen.py            # write all registered puzzles
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMPL = ROOT / "impls"
SAMP = IMPL / "samples"

# -- rules.txt is the single source of truth for metadata ---------------------
CAT = {}
for line in (ROOT / "rules.txt").read_text(encoding="utf-8").splitlines()[1:]:
    f = line.split("\t")
    if len(f) >= 7 and f[0]:
        CAT[f[0]] = {"en": f[2], "zh": f[3], "category": f[5],
                     "subcategory": f[6] if len(f) > 6 else "", "rule": f[-1]}

ENTRIES = {}

# palettes / layer shorthands
SHADE_LAYER = {"id": "shade", "label": "涂黑", "element": "shade", "target": "cell",
               "role": "output", "var": "x", "palette": {"1": "#232733", "2": "#7f8ea3"}}


def num_layer(var="n", label="数字提示", **opts):
    d = {"id": "clue_" + var, "label": label, "element": "number", "target": "cell",
         "role": "input", "var": var, "options": {"min": 0}}
    d.update(opts)
    return d


def circle_layer(var="o", label="圆圈"):
    return {"id": "circle_" + var, "label": label, "element": "circle", "target": "cell",
            "role": "input", "var": var,
            "palette": {"1": "#ffffff", "2": "#232733", "3": "#9aa4b2"}}


def arrow_layer(var="d", label="箭头"):
    return {"id": "arrow_" + var, "label": label, "element": "arrow", "target": "cell",
            "role": "input", "var": var}


REGION_LAYER = {"id": "regions", "label": "区域划分", "element": "region",
                "target": "cell", "role": "input", "var": "__regions"}


def const(name, doc):
    return {"name": name, "kind": "cell", "type": "constant", "doc": doc}


def shade_var():
    return {"name": "x", "kind": "cell", "type": "normal", "domain": [0, 1],
            "doc": "0 = 留白, 1 = 涂黑"}


def add(key, dsl, variables, layers, rows=8, cols=8, uses_regions=False,
        notes="", params=None, sample=None, status="complete", unencoded=None):
    """Register one puzzle.

    `status`    — "complete" or "partial", reported honestly.
    `unencoded` — clue variables that are declared (so the board can hold the
                  real puzzle data) but deliberately not yet constrained. The
                  verifier treats these as expected-dead instead of a bug.
    """
    meta = CAT[key]
    spec = {
        "key": key, "en": meta["en"], "zh": meta["zh"],
        "category": meta["category"], "subcategory": meta["subcategory"],
        "rule": meta["rule"],
        "defaultRows": rows, "defaultCols": cols,
        "usesRegions": uses_regions,
        "variables": variables, "layers": layers,
        "params": params or {}, "notes": notes,
    }
    if unencoded:
        spec["unencodedClues"] = list(unencoded)
    ENTRIES[key] = (spec, dsl.strip() + "\n", sample, status)


def block_regions(rows, cols, h=2, w=2):
    per = (cols + w - 1) // w
    return {f"{r},{c}": (r // h) * per + (c // w) for r in range(rows) for c in range(cols)}


def sample(key, rows=6, cols=6, clues=None, regions=None, params=None, title=""):
    sm = {"puzzle": key, "rows": rows, "cols": cols, "title": title or CAT[key]["zh"],
          "clues": clues or {}}
    if regions:
        sm["regions"] = regions
    if params:
        sm["params"] = params
    return sm


def main():
    import gen as G  # the module object the batches register into
    import gen_shade1  # noqa: F401
    import gen_shade2  # noqa: F401

    entries = G.ENTRIES
    for key, (spec, dsl, sm, status) in entries.items():
        (IMPL / f"{key}.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
        (IMPL / f"{key}.dsl").write_text(dsl, encoding="utf-8")
        if sm is None:
            sm = G.sample(key, regions=G.block_regions(6, 6) if spec["usesRegions"] else None)
        (SAMP / f"{key}.json").write_text(json.dumps(sm, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
    comp = sum(1 for v in entries.values() if v[3] == "complete")
    print(f"wrote {len(entries)} rules  ({comp} complete, {len(entries) - comp} partial)")
    print("keys:", " ".join(entries))


if __name__ == "__main__":
    main()
