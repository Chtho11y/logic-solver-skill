"""Write spec JSON + samples for easy 分区 rules."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tools.scaffold import (  # noqa: E402
    BLACK,
    WHITE,
    clue_arrow,
    clue_circle,
    clue_number,
    layer,
    partition_layer,
    sample,
    shade,
    var,
    write_sample,
    write_spec,
)
from tools.samples import from_grid  # noqa: E402

CC = var("c", "cell", "cc", doc="区域划分")


def _write():
    write_spec(
        "fourcells",
        variables=[CC, var("n", "cell", "constant", doc="此格区域边界边数")],
        layers=[clue_number("n", "边界边数"), partition_layer()],
        rows=8, cols=8,
    )
    write_sample("fourcells", sample(
        "fourcells", 4, 4, title="4x4 四块田",
        clues={"n": from_grid("""
            2 . 2 .
            . . . .
            2 . 2 .
            . . . .
        """)},
    ))

    write_spec(
        "fivecells",
        variables=[CC, var("n", "cell", "constant", doc="此格区域边界边数")],
        layers=[clue_number("n", "边界边数"), partition_layer()],
        rows=8, cols=8,
    )
    write_sample("fivecells", sample(
        "fivecells", 3, 5, title="3x5 三条五格",
        clues={"n": from_grid("""
            3 . 2 . 3
            3 . 2 . 3
            3 . 2 . 3
        """)},
    ))

    write_spec(
        "meadows",
        variables=[CC, var("o", "cell", "constant", doc="1=白圈 2=黑圈")],
        layers=[clue_circle("o", "黑圈"), partition_layer()],
        rows=8, cols=8,
        notes="每个正方形恰好一个黑圈。",
    )
    write_sample("meadows", sample(
        "meadows", 4, 4, title="4x4 四块草地",
        clues={"o": {"0,0": 2, "0,2": 2, "2,0": 2, "2,2": 2}},
    ))

    write_spec(
        "squarejam",
        variables=[CC, var("n", "cell", "constant", doc="正方形边长")],
        layers=[clue_number("n", "边长"), partition_layer()],
        rows=8, cols=8,
    )
    write_sample("squarejam", sample(
        "squarejam", 4, 4, title="4x4 一整块",
        clues={"n": {"1,1": 4}},
    ))

    write_spec(
        "tatamibari",
        variables=[CC, var("s", "cell", "constant", doc="1=横线 2=竖线 3=加号")],
        layers=[
            layer("symbol", "符号", "number", role="input", var="s", min=1, max=3),
            partition_layer(),
        ],
        rows=8, cols=8,
        notes="s: 1=横线(宽>高) 2=竖线(高>宽) 3=加号(正方形)。",
    )
    write_sample("tatamibari", sample(
        "tatamibari", 2, 3, title="2x3 横榻榻米",
        clues={"s": {"0,1": 1}},
    ))

    write_spec(
        "tentaisho",
        variables=[CC, var("o", "cell", "constant", doc="星系中心（格心）")],
        layers=[
            layer(
                "dot", "圆点", "circle", role="input", var="o",
                palette={"1": BLACK, "2": BLACK},
            ),
            partition_layer(),
        ],
        rows=8, cols=8,
        notes="圆点写在格子中心；格线/格点上的圆心未建模。",
    )
    write_sample("tentaisho", sample(
        "tentaisho", 3, 3, title="3x3 一星系",
        clues={"o": {"1,1": 1}},
    ))

    write_spec(
        "kramma",
        variables=[CC, var("o", "cell", "constant", doc="1=白圈 2=黑圈")],
        layers=[clue_circle("o", "圆圈"), partition_layer()],
        rows=8, cols=8,
        notes="分割线为贯通盘面的横平竖直线。",
    )
    write_sample("kramma", sample(
        "kramma", 2, 2, title="2x2 同色两圈",
        clues={"o": {"0,0": 2, "1,1": 2}},
    ))

    write_spec(
        "aho",
        variables=[CC, var("n", "cell", "constant", doc="区域面积")],
        layers=[clue_number("n", "面积"), partition_layer()],
        rows=8, cols=8,
        notes="面积为 3 的倍数时用恰好一个 2x2 缺一角刻画 L 形。",
    )
    write_sample("aho", sample(
        "aho", 2, 3, title="2x3 两个曲尺",
        clues={"n": {"0,0": 3, "1,2": 3}},
    ))

    write_spec(
        "domino-search",
        variables=[
            CC,
            var("n", "cell", "constant", doc="格内数字", dense=True),
        ],
        layers=[clue_number("n", "数字"), partition_layer()],
        rows=8, cols=8,
        params={"defaults": {"tiles": [1, 2]}},
        notes="param tiles 为数字列表；其中数字组成的每个无序数对恰好出现一次。",
    )
    write_sample("domino-search", sample(
        "domino-search", 2, 3, title="2x3 三张骨牌",
        clues={"n": from_grid("""
            1 1 2
            2 2 1
        """)},
        params={"tiles": [1, 2]},
    ))

    write_spec(
        "lapaz",
        variables=[
            var("x", "cell", "normal", (0, 1), "1 = 涂黑"),
            CC,
            var("n", "cell", "constant", doc="行列黑格数"),
        ],
        layers=[clue_number("n", "黑格数"), shade(), partition_layer()],
        rows=8, cols=8,
    )
    write_sample("lapaz", sample(
        "lapaz", 3, 3, title="3x3 一黑",
        clues={"n": {"0,0": 0}},
    ))

    write_spec(
        "compass",
        variables=[
            CC,
            var("k", "cell", "constant", doc="1 = 指南针"),
            var("nu", "cell", "constant", doc="上方格数"),
            var("nd", "cell", "constant", doc="下方格数"),
            var("nl", "cell", "constant", doc="左方格数"),
            var("nr", "cell", "constant", doc="右方格数"),
        ],
        layers=[
            layer("mark", "指南针", "cross", role="input", var="k"),
            layer("nu", "上", "number", role="input", var="nu", min=0),
            layer("nd", "下", "number", role="input", var="nd", min=0),
            layer("nl", "左", "number", role="input", var="nl", min=0),
            layer("nr", "右", "number", role="input", var="nr", min=0),
            partition_layer(),
        ],
        rows=8, cols=8,
    )
    write_sample("compass", sample(
        "compass", 2, 2, title="2x2 一针",
        clues={"k": {"0,0": 1}, "nd": {"0,0": 2}, "nr": {"0,0": 2}},
    ))

    write_spec(
        "sashigane",
        variables=[
            CC,
            var("o", "cell", "constant", doc="转弯圆圈"),
            var("d", "cell", "constant", doc="端点箭头 0-3"),
            var("n", "cell", "constant", doc="区域面积"),
        ],
        layers=[
            clue_circle("o", "转弯"),
            clue_arrow("d", "箭头"),
            clue_number("n", "面积"),
            partition_layer(),
        ],
        rows=8, cols=8,
    )
    write_sample("sashigane", sample(
        "sashigane", 2, 3, title="2x3 两个曲尺",
        clues={"o": {"0,0": 1, "1,2": 1}, "n": {"0,0": 3, "1,2": 3}},
    ))

    write_spec(
        "snakepit",
        variables=[
            CC,
            var("n", "cell", "constant", doc="蛇长"),
            var("o", "cell", "constant", doc="蛇的一端"),
            var("g", "cell", "constant", doc="1 = 灰格（非端点）"),
        ],
        layers=[
            clue_number("n", "蛇长"),
            clue_circle("o", "端点"),
            layer(
                "gray", "灰格", "shade", role="input", var="g",
                palette={"1": "#9aa4b2"},
            ),
            partition_layer(),
        ],
        rows=8, cols=8,
    )
    write_sample("snakepit", sample(
        "snakepit", 2, 3, title="2x3 蛇与骨牌",
        clues={"n": {"0,0": 4, "1,2": 2}, "o": {"0,2": 1, "1,0": 1}},
    ))

    write_spec(
        "wafusuma",
        variables=[
            CC,
            var("k", "edge", "constant", doc="两区面积和"),
        ],
        layers=[
            layer("sum", "面积和", "number", target="edge", role="input", var="k", min=0),
            partition_layer(),
        ],
        rows=8, cols=8,
    )
    write_sample("wafusuma", sample(
        "wafusuma", 2, 2, title="2x2 三加一",
        clues={"k": {"H,1,1": 4, "V,1,1": 4}},
    ))

    write_spec(
        "bdblock",
        variables=[
            CC,
            var("n", "cell", "constant", doc="区域内数字"),
            var("o", "corner", "constant", doc="1 = 黑点（恰三条界）"),
        ],
        layers=[
            clue_number("n", "数字"),
            layer(
                "dot", "黑点", "dot", target="corner", role="input", var="o",
                palette={"1": BLACK},
            ),
            partition_layer(),
        ],
        rows=8, cols=8,
    )
    write_sample("bdblock", sample(
        "bdblock", 2, 2, title="2x2 两行",
        clues={
            "n": from_grid("""
                1 1
                2 2
            """),
            "o": {"1,0": 1, "1,2": 1},
        },
    ))


if __name__ == "__main__":
    _write()
    print("wrote 分区 specs and samples")
