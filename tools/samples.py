"""Write the bundled sample instances in ``impls/samples/``.

Each sample is a small, hand-checked board used by ``python -m tools.check
solve`` as the regression suite for the solvers.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.scaffold import sample, write_sample  # noqa: E402


def from_grid(text: str, blank: str = ".") -> dict[str, int]:
    """Parse a picture into ``{"r,c": value}``, skipping ``blank`` characters."""

    out: dict[str, int] = {}
    for r, line in enumerate(text.strip().splitlines()):
        for c, ch in enumerate(line.split()):
            if ch != blank:
                out[f"{r},{c}"] = int(ch)
    return out


def block_regions(rows: int, cols: int, h: int, w: int) -> dict[str, int]:
    per_row = (cols + w - 1) // w
    return {
        f"{r},{c}": (r // h) * per_row + (c // w)
        for r in range(rows)
        for c in range(cols)
    }


def row_regions(rows: int, cols: int) -> dict[str, int]:
    return {f"{r},{c}": r for r in range(rows) for c in range(cols)}


SAMPLES: dict[str, dict] = {}

SAMPLES["sudoku"] = sample(
    "sudoku", 9, 9,
    title="经典数独",
    clues={"x": from_grid("""
        5 3 . . 7 . . . .
        6 . . 1 9 5 . . .
        . 9 8 . . . . 6 .
        8 . . . 6 . . . 3
        4 . . 8 . 3 . . 1
        7 . . . 2 . . . 6
        . 6 . . . . 2 8 .
        . . . 4 1 9 . . 5
        . . . . 8 . . 7 9
    """)},
)

SAMPLES["nurikabe"] = sample(
    "nurikabe", 5, 5,
    title="5x5 数墙",
    clues={"x": {}, "n": from_grid("""
        2 . . 2 .
        . . . . .
        2 . . 2 .
        . . . . .
        2 . . 2 .
    """)},
)

SAMPLES["hitori"] = sample(
    "hitori", 5, 5,
    title="拉丁方数壹（解为全留白）",
    clues={"n": from_grid("""
        1 2 3 4 5
        2 3 4 5 1
        3 4 5 1 2
        4 5 1 2 3
        5 1 2 3 4
    """)},
)

SAMPLES["norinori"] = sample(
    "norinori", 4, 4,
    title="4x4 海苔",
    regions=block_regions(4, 4, 2, 2),
)

SAMPLES["starbattle"] = sample(
    "starbattle", 5, 5,
    title="每行一星",
    regions=row_regions(5, 5),
    params={"stars": 1},
)

SAMPLES["slither"] = sample(
    "slither", 5, 5,
    title="单格回路",
    clues={"n": {"2,2": 4}},
)

SAMPLES["masyu"] = sample(
    "masyu", 5, 5,
    title="单白珠",
    clues={"o": {"2,2": 1}},
)

SAMPLES["simpleloop"] = sample(
    "simpleloop", 4, 4,
    title="哈密顿回路",
    clues={"w": {}},
)

SAMPLES["nonogram"] = sample(
    "nonogram", 5, 5,
    title="回字数织",
    params={
        "top": [[5], [1, 1], [1, 1, 1], [1, 1], [5]],
        "left": [[5], [1, 1], [1, 1, 1], [1, 1], [5]],
    },
)

SAMPLES["box"] = sample(
    "box", 4, 4,
    title="对角线方阵和",
    params={"left": [1, 2, 3, 4], "top": [1, 2, 3, 4]},
)

SAMPLES["mines"] = sample(
    "mines", 4, 4,
    title="4x4 扫雷",
    clues={"n": from_grid("""
        . 2 . 1
        . . . .
        . . 2 .
        0 . . .
    """)},
)

SAMPLES["yinyang"] = sample(
    "yinyang", 4, 4,
    title="4x4 阴阳",
    clues={"g": {"0,0": 0, "0,3": 1}},
)

SAMPLES["shikaku"] = sample(
    "shikaku", 4, 4,
    title="四块 2x2",
    clues={"n": {"0,0": 4, "0,2": 4, "2,0": 4, "2,2": 4}},
)

SAMPLES["fillomino"] = sample(
    "fillomino", 3, 3,
    title="单区域码牌",
    clues={"n": {"1,1": 9}},
)

SAMPLES["suguru"] = sample(
    "suguru", 4, 4,
    title="2x2 胶囊",
    regions=block_regions(4, 4, 2, 2),
)

SAMPLES["ripple"] = sample(
    "ripple", 4, 4,
    title="2x2 涟漪",
    regions=block_regions(4, 4, 2, 2),
)

SAMPLES["heyawake"] = sample(
    "heyawake", 4, 4,
    title="4x4 数间",
    regions=block_regions(4, 4, 2, 2),
    clues={"n": {"0,0": 1, "0,2": 0, "2,0": 0, "2,2": 1}},
)

SAMPLES["akari"] = sample(
    "akari", 4, 4,
    title="4x4 美术馆",
    clues={"w": {"1,1": 1, "2,2": 1}, "n": {"1,1": 1}},
)

SAMPLES["kurodoko"] = sample(
    "kurodoko", 5, 5,
    title="5x5 田鼠挖洞",
    clues={"n": {"0,0": 5, "4,4": 5}},
)

SAMPLES["chocona"] = sample(
    "chocona", 4, 4,
    title="4x4 巧克力",
    regions=block_regions(4, 4, 2, 2),
    clues={"n": {"0,0": 4, "0,2": 0, "2,0": 0, "2,2": 4}},
)

SAMPLES["aqre"] = sample(
    "aqre", 4, 4,
    title="4x4 黑白无四",
    regions=block_regions(4, 4, 2, 2),
    clues={"n": {"0,0": 2, "0,2": 2, "2,0": 2, "2,2": 2}},
)

SAMPLES["cave"] = sample(
    "cave", 5, 5,
    title="5x5 山洞",
    clues={"n": {"2,2": 5}},
)

SAMPLES["country"] = sample(
    "country", 4, 4,
    title="4x4 周游列国",
    regions=block_regions(4, 4, 2, 2),
)

SAMPLES["doubleback"] = sample(
    "doubleback", 4, 4,
    title="4x4 二次返回",
    regions=block_regions(4, 4, 2, 4),
)

SAMPLES["detour"] = sample(
    "detour", 4, 4,
    title="4x4 绕道",
    regions=block_regions(4, 4, 2, 2),
)

SAMPLES["norinuri_placeholder"] = {}
del SAMPLES["norinuri_placeholder"]


def main() -> int:
    for key, instance in SAMPLES.items():
        write_sample(key, instance)
    print(f"wrote {len(SAMPLES)} sample(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
