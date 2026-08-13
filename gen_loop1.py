"""Write spec JSON + samples for binairo and the easy 回路I rules."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.scaffold import (  # noqa: E402
    LOOP_VAR,
    SHADE_VAR,
    clue_arrow,
    clue_circle,
    clue_number,
    edgeline_layer,
    link_layer,
    region_layer,
    sample,
    shade,
    var,
    write_sample,
    write_spec,
)
from tools.samples import block_regions, from_grid  # noqa: E402

BLOCKS = block_regions(4, 4, 2, 2)
INS_VAR = var("ins", "cell", "normal", (0, 1), "1 = 回路内部")
Y_VAR = var("y", "cell", "normal", (0, 1), "1 = 不在回路上（辅助）")


def _write():
    write_spec(
        "binairo",
        variables=[
            SHADE_VAR,
            var("o", "cell", "constant", doc="1=白圈 2=黑圈"),
        ],
        layers=[clue_circle("o", "给定圆圈"), shade()],
        rows=8, cols=8,
        notes="边长须为偶数。o: 1=白圈须留白，2=黑圈须涂黑。",
    )
    write_sample("binairo", sample(
        "binairo", 4, 4, title="4x4 横竖无三",
        clues={"o": from_grid("""
            2 2 . .
            . . . .
            . . . .
            . . . 2
        """)},
    ))

    write_spec(
        "myopia",
        variables=[
            LOOP_VAR,
            var("a", "cell", "constant", doc="箭头位掩码 1=上 2=下 4=左 8=右"),
        ],
        layers=[clue_number("a", "箭头掩码"), edgeline_layer()],
        rows=8, cols=8,
        notes="a 为方向位掩码，可按位组合（如 9=上+右）。",
    )
    write_sample("myopia", sample(
        "myopia", 4, 4, title="4x4 近视回路",
        clues={"a": {"1,1": 8}},
    ))

    write_spec(
        "swslither",
        variables=[
            LOOP_VAR,
            var("n", "cell", "constant", doc="此格回路边数"),
            var("o", "cell", "constant", doc="1=羊 2=狼"),
            INS_VAR,
        ],
        layers=[
            clue_number(),
            clue_circle("o", "羊/狼"),
            edgeline_layer(),
        ],
        rows=8, cols=8,
        notes="o: 1=羊（回路内）2=狼（回路外）。ins 为内部标记，不绘制。",
    )
    write_sample("swslither", sample(
        "swslither", 4, 4, title="4x4 羊圈数回",
        clues={"n": {"1,1": 3}, "o": {"0,0": 1, "3,3": 2}},
    ))

    write_spec(
        "midloop",
        variables=[LOOP_VAR, var("o", "cell", "constant", doc="黑点")],
        layers=[clue_circle("o", "中点"), link_layer()],
        rows=8, cols=8,
    )
    write_sample("midloop", sample(
        "midloop", 4, 4, title="4x4 中点回路",
        clues={"o": {"1,1": 1, "1,2": 1}},
    ))

    write_spec(
        "geradeweg",
        variables=[
            LOOP_VAR,
            var("o", "cell", "constant", doc="圈"),
            var("n", "cell", "constant", doc="直线段长"),
        ],
        layers=[clue_circle("o", "圈"), clue_number(), link_layer()],
        rows=8, cols=8,
    )
    write_sample("geradeweg", sample(
        "geradeweg", 4, 4, title="4x4 直线回路",
        clues={"o": {"0,1": 1}, "n": {"0,1": 4}},
    ))

    write_spec(
        "dotchi",
        variables=[
            LOOP_VAR,
            var("o", "cell", "constant", doc="1=白圈 2=黑圈"),
        ],
        layers=[region_layer(), clue_circle("o", "圆圈"), link_layer()],
        rows=8, cols=8, uses_regions=True,
    )
    write_sample("dotchi", sample(
        "dotchi", 4, 4, title="4x4 二择回路",
        clues={"o": from_grid("""
            1 . 1 .
            . 2 . 2
            1 . 1 .
            . 2 . 2
        """)},
        regions=BLOCKS,
    ))

    write_spec(
        "dotchi2",
        variables=[
            LOOP_VAR,
            var("o", "cell", "constant", doc="1=白圈 2=黑圈"),
        ],
        layers=[region_layer(), clue_circle("o", "圆圈"), link_layer()],
        rows=8, cols=8, uses_regions=True,
        notes="每区至少一圈；合成空盘在无圈区域会无解。",
    )
    write_sample("dotchi2", sample(
        "dotchi2", 4, 4, title="4x4 dotchi2",
        clues={"o": from_grid("""
            . 1 1 .
            . . . .
            . . . .
            2 . . 2
        """)},
        regions=BLOCKS,
    ))

    write_spec(
        "balance",
        variables=[
            LOOP_VAR,
            var("o", "cell", "constant", doc="1=白圈 2=黑圈"),
            var("n", "cell", "constant", doc="两臂长度和"),
        ],
        layers=[clue_circle("o", "圆圈"), clue_number(), link_layer()],
        rows=8, cols=8,
    )
    write_sample("balance", sample(
        "balance", 4, 4, title="4x4 平衡回路",
        clues={"o": {"1,1": 1}, "n": {"1,1": 4}},
    ))

    write_spec(
        "nanameguri",
        variables=[
            LOOP_VAR,
            var("g", "cell", "constant", doc="1=\\ 2=/"),
        ],
        layers=[region_layer(), clue_number("g", "对角线"), link_layer()],
        rows=8, cols=8, uses_regions=True,
        notes="g: 1=主对角线（不穿过则走 上+右 或 左+下），2=副对角线（上+左 或 右+下）。",
    )
    write_sample("nanameguri", sample(
        "nanameguri", 4, 4, title="4x4 nanameguri",
        clues={"g": {"1,1": 1, "1,2": 2}},
        regions=block_regions(4, 4, 4, 2),
    ))

    write_spec(
        "moonsun",
        variables=[
            LOOP_VAR,
            var("o", "cell", "constant", doc="1=太阳 2=月亮"),
        ],
        layers=[region_layer(), clue_circle("o", "日月"), link_layer()],
        rows=8, cols=8, uses_regions=True,
    )
    write_sample("moonsun", sample(
        "moonsun", 4, 4, title="4x4 日月交替",
        clues={"o": from_grid("""
            1 . 2 .
            . . . .
            2 . 1 .
            . . . .
        """)},
        regions=BLOCKS,
    ))

    write_spec(
        "castle",
        variables=[
            LOOP_VAR,
            var("o", "cell", "constant", doc="1=白格(内) 2=黑格(外)"),
            var("n", "cell", "constant", doc="该方向回路格数"),
            var("d", "cell", "constant", doc="箭头方向"),
            INS_VAR,
            Y_VAR,
        ],
        layers=[
            clue_circle("o", "黑白格"),
            clue_arrow(),
            clue_number(),
            link_layer(),
        ],
        rows=8, cols=8,
        notes="箭头数字按该方向上回路经过的格子计数。ins/y 为内部判定辅助变量。",
    )
    write_sample("castle", sample(
        "castle", 4, 4, title="4x4 城堡墙",
        clues={
            "o": {"1,1": 1, "0,3": 2},
            "n": {"0,3": 3},
            "d": {"0,3": 2},
        },
    ))


if __name__ == "__main__":
    _write()
    print("wrote binairo + 回路I specs and samples")
