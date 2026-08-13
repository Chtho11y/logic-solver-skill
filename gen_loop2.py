"""Write spec JSON + samples for easy 回路II rules and hidato."""

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
    layer,
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
Y_VAR = var("y", "cell", "normal", (0, 1), "1 = 不在回路上（辅助）")


def _write():
    write_spec(
        "yajilin-regions",
        variables=[LOOP_VAR, SHADE_VAR, var("n", "cell", "constant", doc="区域内黑格数")],
        layers=[region_layer(), clue_number(), shade(), link_layer()],
        rows=8, cols=8, uses_regions=True,
    )
    write_sample("yajilin-regions", sample(
        "yajilin-regions", 4, 4, title="4x4 仙人指区",
        clues={"n": from_grid("""
            1 . 0 .
            . . . .
            1 . 0 .
            . . . .
        """)},
        regions=BLOCKS,
    ))

    write_spec(
        "koburin",
        variables=[LOOP_VAR, SHADE_VAR, var("n", "cell", "constant", doc="四邻黑格数")],
        layers=[clue_number(), shade(), link_layer()],
        rows=8, cols=8,
    )
    write_sample("koburin", sample(
        "koburin", 4, 4, title="4x4 仙人指邻",
        clues={"n": {"1,1": 1}},
    ))

    write_spec(
        "nuriloop",
        variables=[LOOP_VAR, Y_VAR, var("n", "cell", "constant", doc="未经过连通组格数")],
        layers=[clue_number(), link_layer()],
        rows=8, cols=8,
        notes="y 为未经过标记，不绘制。",
    )
    write_sample("nuriloop", sample(
        "nuriloop", 4, 4, title="4x4 数墙回路",
        clues={"n": {"0,0": 2, "3,3": 2}},
    ))

    write_spec(
        "alternate",
        variables=[LOOP_VAR, var("o", "cell", "constant", doc="1=白圈 2=黑圈")],
        layers=[clue_circle("o", "圆圈"), link_layer()],
        rows=8, cols=8,
        notes="部分实现：仅约束被回路边直接相连的圆圈异色。沿回路隔格连续的同色圆圈未编码。",
        unencoded=[],
    )
    write_sample("alternate", sample(
        "alternate", 4, 4, title="4x4 交替回路",
        clues={"o": from_grid("""
            1 . . 2
            . . . .
            . . . .
            2 . . 1
        """)},
    ))

    write_spec(
        "nothing",
        variables=[LOOP_VAR],
        layers=[region_layer(), link_layer()],
        rows=8, cols=8, uses_regions=True,
    )
    write_sample("nothing", sample(
        "nothing", 4, 4, title="4x4 满或空",
        regions=BLOCKS,
    ))

    write_spec(
        "kurarin",
        variables=[
            SHADE_VAR,
            var("c", "corner", "constant", doc="1=留白多 2=涂黑多 3=一样多"),
        ],
        layers=[
            layer(
                "dots", "格点提示", "number", target="corner", var="c",
                min=1, max=3,
            ),
            shade(),
        ],
        rows=8, cols=8,
        notes="提示在格点上，与 creek 相同。留白必须形成单条回路。",
    )
    write_sample("kurarin", sample(
        "kurarin", 4, 4, title="4x4 黑暗回路",
        clues={"c": {"1,1": 2, "3,3": 1}},
    ))

    write_spec(
        "mukkonn",
        variables=[
            LOOP_VAR,
            var("n", "cell", "constant", doc="直行格数"),
            var("d", "cell", "constant", doc="三角形方向"),
        ],
        layers=[clue_arrow(), clue_number(), link_layer()],
        rows=8, cols=8,
        notes="每格至多一个三角形（d+n）。",
    )
    write_sample("mukkonn", sample(
        "mukkonn", 4, 4, title="4x4 四向回路",
        clues={"n": {"0,0": 3}, "d": {"0,0": 3}},
    ))

    write_spec(
        "hidato",
        variables=[
            var("x", "cell", "normal", (1, 36), "1..N"),
            var("n", "cell", "constant", doc="已给数字"),
        ],
        layers=[
            clue_number("n", "已给数字"),
            layer("answer", "填数", "number", role="output", var="x"),
        ],
        rows=6, cols=6,
        notes="domain 上限 36，默认盘面不超过 6x6。数字八邻域相连。",
    )
    write_sample("hidato", sample(
        "hidato", 3, 3, title="3x3 一笔画",
        clues={"n": from_grid("""
            1 . 3
            . . .
            . . 9
        """)},
    ))


if __name__ == "__main__":
    _write()
    print("wrote 回路II + hidato specs and samples")
