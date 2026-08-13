"""Write spec JSON + samples for remaining 回路I / 回路II rules."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tools.scaffold import (  # noqa: E402
    LOOP_VAR,
    SHADE_VAR,
    clue_arrow,
    clue_circle,
    clue_number,
    edgeline_layer,
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
TERRAIN = var("w", "cell", "constant", doc="1 = 特殊地形")
ICE = var("t", "cell", "constant", doc="1 = 冰格")
WALL = var("w", "edge", "constant", doc="1 = 粗格线")
GATE = var("g", "cell", "constant", doc="1 = 关卡")
PLUS = var("g", "cell", "constant", doc="1 = 加号")
F_VAR = var("f", "edge", "normal", (0, 1), "1 = 第二条回路")
X_VAR = var("x", "cell", "normal", (0, 3), "0空 1=\\ 2=/ 3=交叉")
S_VAR = var("s", "cell", "constant", doc="管道形状 1横 2竖 3交叉 4上左 5上右 6下左 7下右")
N2 = var("n2", "cell", "constant", doc="第二段长")
N3 = var("n3", "cell", "constant", doc="第三段长")
N4 = var("n4", "cell", "constant", doc="第四段长")


def given_shade(name="w", label="地形", color="#4a90d9"):
    return layer("given_" + name, label, "shade", role="input", var=name, palette={"1": color})


def _write():
    write_spec(
        "lineofsight",
        variables=[
            LOOP_VAR,
            var("n", "cell", "constant", doc="最近线段长度"),
            var("d", "cell", "constant", doc="箭头方向"),
        ],
        layers=[clue_arrow(), clue_number(), edgeline_layer()],
        rows=8, cols=8,
        notes="格线回路。数字=该方向最近一条回路线段的长度（非格距）。",
    )
    write_sample("lineofsight", sample(
        "lineofsight", 4, 4, title="4x4 视线",
        clues={"n": {"1,1": 4}, "d": {"1,1": 0}},
    ))

    write_spec(
        "waterwalk",
        variables=[LOOP_VAR, TERRAIN, var("n", "cell", "constant", doc="白段长度")],
        layers=[given_shade("w", "水格", "#4a90d9"), clue_number(), link_layer()],
        rows=8, cols=8,
        notes="部分实现：水格沿回路连续不超过 2；数字格必经且非水。n=1 已编码；n>1 沿回路白段长度未编码。",
        unencoded=[],
    )
    write_sample("waterwalk", sample(
        "waterwalk", 3, 3, title="3x3 水面行者",
        clues={"n": {"0,0": 8}, "w": {}},
    ))

    write_spec(
        "firewalk",
        variables=[LOOP_VAR, TERRAIN, var("n", "cell", "constant", doc="白段长度")],
        layers=[given_shade("w", "火格", "#c0392b"), clue_number(), link_layer()],
        rows=8, cols=8,
        notes="部分实现：火格必转弯，允许度4。数字格必经且非火。n=1 已编码；n>1 沿回路白段长度未编码。",
        unencoded=[],
    )
    write_sample("firewalk", sample(
        "firewalk", 3, 3, title="3x3 烈焰行者",
        clues={"n": {"0,0": 8}, "w": {}},
    ))

    write_spec(
        "disloop",
        variables=[
            LOOP_VAR,
            var("n", "cell", "constant", doc="线段长度"),
            var("d", "cell", "constant", doc="箭头方向"),
        ],
        layers=[clue_arrow(), clue_number(), link_layer()],
        rows=8, cols=8,
        notes="部分实现：提示格不在回路上；单数=箭头前方格的直线段长。多段无序多重集未编码。",
        unencoded=[],
    )
    write_sample("disloop", sample(
        "disloop", 4, 4, title="4x4 乱序回路",
        clues={"n": {"1,1": 4}, "d": {"1,1": 2}},
    ))

    write_spec(
        "icewalk",
        variables=[LOOP_VAR, TERRAIN, var("n", "cell", "constant", doc="白段长度")],
        layers=[given_shade("w", "冰格", "#7fdbff"), clue_number(), link_layer()],
        rows=8, cols=8,
        notes="部分实现：冰格不转弯可自交，白格不自交。数字格必经且非冰。n=1 已编码；n>1 沿回路白段长度未编码。",
        unencoded=[],
    )
    write_sample("icewalk", sample(
        "icewalk", 3, 3, title="3x3 冰宫行者",
        clues={"n": {"0,0": 8}, "w": {}},
    ))

    write_spec(
        "orbital",
        variables=[
            LOOP_VAR,
            var("o", "cell", "constant", doc="1=白圈 2=黑圈"),
            var("n", "cell", "constant", doc="该回路白圈数"),
        ],
        layers=[clue_circle("o", "圆圈"), clue_number(), link_layer()],
        rows=8, cols=8,
        notes="矩形回路可交叉。白圈在周界上，黑圈在恰好一个矩形内部，数字=该矩形周界白圈数。",
    )
    write_sample("orbital", sample(
        "orbital", 3, 3, title="3x3 行星轨道",
        clues={"o": {"0,0": 1, "1,1": 2}, "n": {"1,1": 1}},
    ))

    write_spec(
        "wbloop",
        variables=[LOOP_VAR, var("o", "cell", "constant", doc="1=白圈 2=黑圈")],
        layers=[clue_circle("o", "圆圈"), link_layer()],
        rows=8, cols=8,
        notes="部分实现：经过所有圆圈；同一横/竖直线段上的圆圈必须同色。沿回路拐弯间隔的连续圆圈未完全编码。",
        unencoded=[],
    )
    write_sample("wbloop", sample(
        "wbloop", 4, 4, title="4x4 黑白回路",
        clues={"o": {"0,0": 1, "0,3": 1}},
    ))

    write_spec(
        "reflect",
        variables=[
            LOOP_VAR,
            var("o", "cell", "constant", doc="1=三角形 2=十字"),
            var("d", "cell", "constant", doc="0上右 1下右 2下左 3上左"),
            var("n", "cell", "constant", doc="两臂格子总数"),
        ],
        layers=[clue_circle("o", "三角/十字"), clue_arrow(), clue_number(), link_layer()],
        rows=8, cols=8,
        notes="仅在十字格自交；三角形处按 d 直角转弯。数字=两臂格子数（含本格）。",
    )
    write_sample("reflect", sample(
        "reflect", 2, 2, title="2x2 反射回路",
        clues={"o": {"0,0": 1}, "d": {"0,0": 1}, "n": {"0,0": 3}},
    ))

    write_spec(
        "slalom",
        variables=[
            LOOP_VAR,
            var("o", "cell", "constant", doc="1=起点圆圈"),
            TERRAIN,
            GATE,
            var("n", "cell", "constant", doc="关卡总数"),
            var("d", "cell", "constant", doc="箭头方向"),
        ],
        layers=[
            given_shade("w", "黑格", "#232733"),
            given_shade("g", "关卡", "#9aa4b2"),
            clue_circle("o", "圆圈"),
            clue_arrow(),
            clue_number(),
            link_layer(),
        ],
        rows=8, cols=8,
        notes="部分实现：不经黑格、经过圆圈、关卡直行；圆圈数字=关卡数。有向次序未编码。",
        unencoded=["d"],
    )
    write_sample("slalom", sample(
        "slalom", 3, 3, title="3x3 巡行通关",
        clues={"o": {"0,0": 1}, "w": {}, "g": {}, "n": {}, "d": {}},
    ))

    write_spec(
        "crossstitch",
        variables=[
            X_VAR,
            var("w", "cell", "constant", doc="1=黑格"),
            var("n", "cell", "constant", doc="圆圈角数或箭头交叉数"),
            var("d", "cell", "constant", doc="箭头方向"),
        ],
        layers=[
            given_shade("w", "黑格", "#232733"),
            clue_arrow(),
            clue_number(),
            layer("diag", "对角线", "number", role="output", var="x"),
        ],
        rows=8, cols=8,
        notes="部分实现：对角线 0/\\//交叉，格点度 0 或 2，交叉不相邻，圆圈/箭头数字已编码。恰好两条回路未强制。",
        unencoded=[],
    )
    write_sample("crossstitch", sample(
        "crossstitch", 2, 2, title="2x2 十字绣",
        clues={"w": {}, "n": {}, "d": {}},
    ))

    write_spec(
        "bhaibahan",
        variables=[
            LOOP_VAR,
            var("o", "cell", "constant", doc="1=圆圈"),
            var("n", "cell", "constant", doc="连续直行或转弯格数"),
        ],
        layers=[clue_circle("o", "圆圈"), clue_number(), link_layer()],
        rows=8, cols=8,
        notes="部分实现：相邻圆圈一直行一转弯；直行数字=直线段内部格数。转弯数字仅 n=1。",
        unencoded=[],
    )
    write_sample("bhaibahan", sample(
        "bhaibahan", 4, 4, title="4x4 同胞回路",
        clues={"o": {"0,0": 1, "0,1": 1}, "n": {}},
    ))

    write_spec(
        "tapaloop",
        variables=[
            LOOP_VAR,
            var("n", "cell", "constant", doc="第一段长"),
            N2, N3, N4,
        ],
        layers=[clue_number(), link_layer()],
        rows=8, cols=8,
        notes="部分实现：单数提示为八邻域恰好一段连续；多段仅约束总和与段数，无序长度一一对应未编码。",
    )
    write_sample("tapaloop", sample(
        "tapaloop", 3, 3, title="3x3 土派回路",
        clues={"n": {"1,1": 8}},
    ))

    write_spec(
        "nagare",
        variables=[
            LOOP_VAR,
            TERRAIN,
            var("d", "cell", "constant", doc="箭头方向"),
        ],
        layers=[
            given_shade("w", "黑格", "#232733"),
            clue_arrow(),
            link_layer(),
        ],
        rows=8, cols=8,
        notes="部分实现：不经黑格；白格箭头处沿轴直行；风扇下风若在回路上则含顺风边。有向逆风/进入后转向未编码。",
        unencoded=[],
    )
    write_sample("nagare", sample(
        "nagare", 3, 3, title="3x3 吹风机回路",
        clues={"w": {"2,2": 1}, "d": {"0,1": 3}},
    ))

    write_spec(
        "ringring",
        variables=[LOOP_VAR, TERRAIN],
        layers=[given_shade("w", "黑格", "#232733"), link_layer()],
        rows=8, cols=8,
        notes="矩形回路覆盖每个空格；可交叉不可共边/共角。",
    )
    write_sample("ringring", sample(
        "ringring", 2, 2, title="2x2 环环相扣",
        clues={"w": {}},
    ))

    write_spec(
        "pipelink",
        variables=[LOOP_VAR, S_VAR],
        layers=[clue_number("s", "管道形状"), link_layer()],
        rows=8, cols=8,
        notes="s: 1=横 2=竖 3=交叉 4=上左 5=上右 6=下左 7=下右。经过全部格子。",
    )
    write_sample("pipelink", sample(
        "pipelink", 2, 2, title="2x2 管道回路",
        clues={"s": {}},
    ))

    write_spec(
        "maxi",
        variables=[LOOP_VAR, var("n", "cell", "constant", doc="最长访问段")],
        layers=[region_layer(), clue_number(), link_layer()],
        rows=8, cols=8, uses_regions=True,
        notes="部分实现：哈密顿回路 + 区域进出次数与最长段的鸽笼不等式。未强制某次经过恰好达到 n。",
        unencoded=[],
    )
    write_sample("maxi", sample(
        "maxi", 2, 2, title="2x2 极大回路",
        clues={"n": {"0,0": 4}},
        regions=block_regions(2, 2, 2, 2),
    ))

    write_spec(
        "trainstations",
        variables=[LOOP_VAR, var("n", "cell", "constant", doc="车站编号")],
        layers=[clue_number(), link_layer()],
        rows=8, cols=8,
        notes="部分实现：经过全部格子；仅数字格可自交；数字格不转弯。按 1..k 顺序经过未编码。",
        unencoded=[],
    )
    write_sample("trainstations", sample(
        "trainstations", 4, 4, title="4x4 铁轨",
        clues={"n": {"0,1": 1, "0,2": 2}},
    ))

    write_spec(
        "barns",
        variables=[LOOP_VAR, ICE, WALL],
        layers=[
            given_shade("t", "冰格", "#7fdbff"),
            layer("walls", "粗格线", "edgeline", target="edge", role="input", var="w"),
            link_layer(),
        ],
        rows=8, cols=8,
        notes="经过全部格子。粗格线不可穿过。冰格不转弯可自交。",
    )
    write_sample("barns", sample(
        "barns", 2, 2, title="2x2 冰宫回路",
        clues={"t": {}, "w": {}},
    ))

    write_spec(
        "vertigo",
        variables=[LOOP_VAR],
        layers=[link_layer()],
        rows=8, cols=8,
        notes="部分实现：经过全部格子，允许自交。沿回路转弯方向全局一致未编码。",
        unencoded=[],
    )
    write_sample("vertigo", sample(
        "vertigo", 2, 2, title="2x2 晕头转向",
    ))

    write_spec(
        "doubleornothing",
        variables=[LOOP_VAR, F_VAR, PLUS],
        layers=[
            given_shade("g", "加号", "#c0392b"),
            link_layer("e", "回路一"),
            layer("loop2", "回路二", "link", target="edge", role="output", var="f"),
        ],
        rows=8, cols=8,
        notes="两条回路不共边。空格恰好一条经过；加号格要么交叉要么都不用。",
    )
    write_sample("doubleornothing", sample(
        "doubleornothing", 4, 4, title="4x4 双或无",
        clues={"g": from_grid("""
            . . 1 1
            . . 1 1
            1 1 . .
            1 1 . .
        """)},
    ))

    write_spec(
        "railpool",
        variables=[LOOP_VAR, var("n", "cell", "constant", doc="直线段长度")],
        layers=[region_layer(), clue_number(), link_layer()],
        rows=8, cols=8, uses_regions=True,
        notes="区域内数字是与该区域相交的直线段长度集合，互不重复。问号未编码。",
    )
    write_sample("railpool", sample(
        "railpool", 2, 2, title="2x2 轨道库",
        clues={"n": {"0,0": 2}},
        regions=block_regions(2, 2, 2, 2),
    ))

    write_spec(
        "nagenawa",
        variables=[LOOP_VAR, var("n", "cell", "constant", doc="区域内经过格数")],
        layers=[region_layer(), clue_number(), link_layer()],
        rows=8, cols=8, uses_regions=True,
        notes="矩形回路可交叉不可共角。数字=区域内至少被一条回路经过的格数。",
    )
    write_sample("nagenawa", sample(
        "nagenawa", 2, 2, title="2x2 套索",
        clues={"n": {"0,0": 4}},
        regions=block_regions(2, 2, 2, 2),
    ))


if __name__ == "__main__":
    _write()
    print("wrote remaining 回路I/II specs and samples")
