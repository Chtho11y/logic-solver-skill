"""Write spec JSON + samples for easy 放置 rules: magnets, gaps, dosufuwa."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tools.scaffold import (  # noqa: E402
    BLACK,
    WHITE,
    layer,
    outside_layer,
    region_layer,
    sample,
    shade,
    var,
    write_sample,
    write_spec,
)
from tools.samples import block_regions  # noqa: E402

PLUS = "#c0392b"
MINUS = "#2980b9"


def _domino_rows(rows: int, cols: int) -> dict[str, int]:
    """Horizontal 1x2 regions covering the board (cols must be even)."""

    return {f"{r},{c}": r * (cols // 2) + (c // 2) for r in range(rows) for c in range(cols)}


def _place_two_stars(n: int) -> list[tuple[int, int]] | None:
    """One (c1, c2) pair per row: 2 stars/row/col, no 8-adjacency."""

    cols_used = [0] * n
    rows: list[tuple[int, int]] = []

    def ok(r: int, c: int) -> bool:
        if cols_used[c] >= 2:
            return False
        for pr, (a, b) in enumerate(rows):
            if abs(pr - r) <= 1 and min(abs(a - c), abs(b - c)) <= 1:
                return False
        return True

    def rec(r: int) -> bool:
        if r == n:
            return True
        for c1 in range(n):
            if not ok(r, c1):
                continue
            for c2 in range(c1 + 2, n):
                if not ok(r, c2):
                    continue
                if abs(c1 - c2) <= 1:
                    continue
                rows.append((c1, c2))
                cols_used[c1] += 1
                cols_used[c2] += 1
                if rec(r + 1):
                    return True
                cols_used[c1] -= 1
                cols_used[c2] -= 1
                rows.pop()
        return False

    if rec(0):
        return rows
    return None


def _gaps_from_pairs(pairs: list[tuple[int, int]], n: int) -> tuple[list[int], list[int]]:
    left = [b - a - 1 for a, b in pairs]
    col_rows: list[list[int]] = [[] for _ in range(n)]
    for r, (a, b) in enumerate(pairs):
        col_rows[a].append(r)
        col_rows[b].append(r)
    top = []
    for rows_here in col_rows:
        rows_here.sort()
        top.append(rows_here[1] - rows_here[0] - 1)
    return left, top


def _write():
    write_spec(
        "magnets",
        variables=[var("x", "cell", "normal", (0, 2), "0=空 1=+ 2=-")],
        layers=[
            region_layer(),
            outside_layer("outside", "正/负号个数", sides=("top", "bottom", "left", "right")),
            layer(
                "signs", "磁铁", "shade", role="output", var="x",
                palette={"1": PLUS, "2": MINUS},
            ),
        ],
        rows=8, cols=8, uses_regions=True,
        params={"defaults": {"top": [], "bottom": [], "left": [], "right": []}},
        notes="left/top = 正号个数；right/bottom = 负号个数。区域均为骨牌。",
    )
    write_sample("magnets", sample(
        "magnets", 2, 2, title="2x2 一对磁铁",
        regions=_domino_rows(2, 2),
        params={
            "left": [1, 1],
            "right": [1, 1],
            "top": [1, 1],
            "bottom": [1, 1],
        },
    ))

    pairs = _place_two_stars(8)
    if pairs is None:
        raise SystemExit("could not place 8x8 gaps stars")
    left, top = _gaps_from_pairs(pairs, 8)
    write_spec(
        "gaps",
        variables=[var("x", "cell", "normal", (0, 1), "1 = 星")],
        layers=[
            outside_layer("outside", "两星间距", sides=("top", "left")),
            layer("stars", "星星", "star", role="output", var="x"),
        ],
        rows=8, cols=8,
        params={"defaults": {"top": [], "left": []}},
        notes="每行每列两星，八邻域不相接。盘外数字不含两星本身。",
    )
    write_sample("gaps", sample(
        "gaps", 8, 8, title="8x8 空隙",
        params={"left": left, "top": top},
    ))

    write_spec(
        "dosufuwa",
        variables=[
            var("x", "cell", "normal", (0, 2), "0=空 1=气球 2=铅球"),
            var("w", "cell", "constant", doc="1 = 黑色单元格"),
        ],
        layers=[
            region_layer(),
            shade("w", "黑色单元格", role="input"),
            layer(
                "circles", "气球/铅球", "circle", role="output", var="x",
                palette={"1": WHITE, "2": BLACK},
            ),
        ],
        rows=8, cols=8, uses_regions=True,
        notes="x: 1=气球○ 2=铅球●。铅球下落、气球上浮，可叠在同类或黑格上。",
    )
    write_sample("dosufuwa", sample(
        "dosufuwa", 2, 2, title="2x2 一球一铅",
        regions=block_regions(2, 2, 2, 2),
        clues={"w": {}},
    ))


if __name__ == "__main__":
    _write()
    print("wrote 放置 specs and samples")
    print("gaps pairs:", _place_two_stars(8))
