"""Write spec JSON + sample instances for the 涂黑III rules added this round."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.scaffold import (  # noqa: E402
    SHADE_VAR,
    clue_arrow,
    clue_circle,
    clue_number,
    outside_layer,
    region_layer,
    sample,
    shade,
    var,
    write_sample,
    write_spec,
)
from tools.samples import block_regions, from_grid  # noqa: E402

BLOCKS_2x2 = block_regions(4, 4, 2, 2)


def _write():
    write_spec(
        "batten",
        variables=[
            SHADE_VAR,
            var("m", "cell", "constant", doc="2x2 棋盘格标记（写在左上格）"),
        ],
        layers=[
            outside_layer("outside", "行列涂黑数", param="outside", sides=("top", "left")),
            clue_circle("m", "棋盘格 2x2"),
            shade(),
        ],
        rows=6, cols=6,
        params={"defaults": {"top": [], "left": []}},
        notes="m 标在 2×2 的左上格。标记与棋盘格 2×2 双射。",
    )
    write_sample("batten", sample(
        "batten", 4, 4, title="4x4 双色蛋糕",
        clues={"m": from_grid("""
            . . . .
            . 1 . .
            . . . .
            . . . .
        """)},
        params={"top": [2, 2, 2, 2], "left": [2, 2, 2, 2]},
    ))

    write_spec(
        "tawa",
        variables=[SHADE_VAR, var("n", "cell", "constant", doc="周围（除正上）黑格数")],
        layers=[clue_number("n", "邻黑数"), shade()],
        rows=8, cols=8,
        notes="邻域为八邻域去掉正上方一格（内部最多 7 格；规则文「六格」按边角折减理解）。",
    )
    write_sample("tawa", sample(
        "tawa", 4, 4, title="4x4 砖墙",
        clues={"n": from_grid("""
            . . . .
            . 2 . .
            . . . .
            . . . .
        """)},
    ))

    write_spec(
        "cocktail",
        variables=[SHADE_VAR, var("n", "cell", "constant", doc="区域内涂黑格数")],
        layers=[region_layer(), clue_number(), shade()],
        rows=8, cols=8, uses_regions=True,
    )
    write_sample("cocktail", sample(
        "cocktail", 4, 4, title="4x4 鸡尾酒灯",
        clues={"n": from_grid("""
            2 . 1 .
            . . . .
            1 . 2 .
            . . . .
        """)},
        regions=BLOCKS_2x2,
    ))

    write_spec(
        "martini",
        variables=[
            SHADE_VAR,
            var("o", "cell", "constant", doc="1=白圈 2=黑圈"),
            var("n", "cell", "constant", doc="白圈所在留白组中的白圈数"),
        ],
        layers=[
            region_layer(),
            clue_circle("o", "圆圈"),
            clue_number("n", "白圈计数"),
            shade(),
        ],
        rows=8, cols=8, uses_regions=True,
        notes="o: 1=白圈须留白，2=黑圈须涂黑（与 masyu/isowatari 一致）。",
    )
    write_sample("martini", sample(
        "martini", 4, 4, title="4x4 马提尼",
        clues={
            "o": from_grid("""
                . . . .
                . 1 . 1
                . . . .
                . . . .
            """),
            "n": from_grid("""
                . . . .
                . 2 . .
                . . . .
                . . . .
            """),
        },
        regions=BLOCKS_2x2,
    ))

    write_spec(
        "mrtile",
        variables=[SHADE_VAR, var("n", "cell", "constant", doc="所在黑组面积")],
        layers=[clue_number(), shade()],
        rows=8, cols=8,
        notes="部分实现：数字=黑组面积，且每组须对角贴上另一组。未编码：对角伙伴须与本组全等。",
    )
    write_sample("mrtile", sample(
        "mrtile", 4, 4, title="4x4 复制瓦片",
        clues={"n": from_grid("""
            2 . . .
            . . 2 .
            . . . .
            . . . .
        """)},
    ))

    write_spec(
        "ququ",
        variables=[SHADE_VAR, var("n", "cell", "constant", doc="所在留白组格数")],
        layers=[clue_number(), shade()],
        rows=8, cols=8,
        notes="部分实现：留白组恰一数字且面积匹配（类数墙）。未编码：对角接触的黑组不能全等。",
    )
    write_sample("ququ", sample(
        "ququ", 5, 5, title="5x5 区区",
        clues={"n": from_grid("""
            2 . . 2 .
            . . . . .
            . . 1 . .
            . . . . .
            2 . . 2 .
        """)},
    ))

    write_spec(
        "chainedb",
        variables=[SHADE_VAR, var("n", "cell", "constant", doc="所在黑组面积，-1=问号")],
        layers=[clue_number(), shade()],
        rows=8, cols=8,
        notes="n<0 表示问号，不限制该组面积。未编码：同一 8-链内两组不能全等。",
    )
    write_sample("chainedb", sample(
        "chainedb", 4, 4, title="4x4 区块链",
        clues={"n": from_grid("""
            2 . . .
            . . . .
            . . . .
            . 2 . .
        """)},
    ))

    write_spec(
        "kuroclone",
        variables=[
            SHADE_VAR,
            var("n", "cell", "constant", doc="指向邻格黑组面积"),
            var("d", "cell", "constant", doc="箭头方向 0=上 1=下 2=左 3=右"),
        ],
        layers=[region_layer(), clue_arrow(), clue_number(), shade()],
        rows=8, cols=8, uses_regions=True,
        notes="部分实现：每区恰两组、提示指向邻格黑组面积。未编码：区内两组须全等。",
    )
    write_sample("kuroclone", sample(
        "kuroclone", 4, 4, title="4x4 黑块克隆",
        clues={
            "n": from_grid("""
                . 1 . .
                . . . .
                . . . .
                . . . .
            """),
            "d": from_grid("""
                . 3 . .
                . . . .
                . . . .
                . . . .
            """),
        },
        regions=BLOCKS_2x2,
    ))

    write_spec(
        "stostone",
        variables=[SHADE_VAR, var("n", "cell", "constant", doc="区域内涂黑格数")],
        layers=[region_layer(), clue_number(), shade()],
        rows=8, cols=8, uses_regions=True,
        notes="行数应为偶数；各组刚体下落恰好覆盖下半盘。",
    )
    write_sample("stostone", sample(
        "stostone", 4, 4, title="4x4 垒石",
        clues={"n": from_grid("""
            2 . 2 .
            . . . .
            2 . 2 .
            . . . .
        """)},
        regions=BLOCKS_2x2,
    ))

    write_spec(
        "interbd",
        variables=[
            SHADE_VAR,
            var("k", "cell", "constant", doc="提示颜色（任意正整数标签）"),
            var("n", "cell", "constant", doc="四邻黑格数"),
        ],
        layers=[
            clue_circle("k", "提示颜色"),
            clue_number("n", "邻黑数"),
            shade(),
        ],
        rows=8, cols=8,
    )
    write_sample("interbd", sample(
        "interbd", 4, 4, title="4x4 国界线",
        clues={
            "k": from_grid("""
                1 . . 2
                . . . .
                . . . .
                . . . .
            """),
            "n": from_grid("""
                0 . . 1
                . . . .
                . . . .
                . . . .
            """),
        },
    ))

    write_spec(
        "evolmino",
        variables=[
            SHADE_VAR,
            var("a", "cell", "constant", doc="箭头编号（同号同箭）"),
            var("d", "cell", "constant", doc="箭头方向"),
        ],
        layers=[clue_arrow("d", "箭头方向"), clue_number("a", "箭头编号"), shade()],
        rows=8, cols=8,
        notes="部分实现：每组恰一箭头格、箭上后组比前组多一格。未编码：后组须为前组的平移。每条箭为正线，d 写在每个箭头格上。",
    )
    write_sample("evolmino", sample(
        "evolmino", 4, 4, title="4x4 生长方块",
        clues={
            "a": from_grid("""
                1 . . .
                . . . .
                1 . . .
                . . . .
            """),
            "d": from_grid("""
                1 . . .
                . . . .
                1 . . .
                . . . .
            """),
        },
    ))


if __name__ == "__main__":
    _write()
    print("wrote 涂黑III specs and samples")
