"""Write spec JSON + samples for remaining 放置 / 分区 rules."""

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
    outside_layer,
    partition_layer,
    region_layer,
    sample,
    shade,
    var,
    write_sample,
    write_spec,
)
from tools.samples import block_regions, from_grid  # noqa: E402

CC = var("c", "cell", "cc", doc="区域划分")
GRAY = "#9aa4b2"


def _write():
    # ---- 放置 ----------------------------------------------------------------
    write_spec(
        "statuepark",
        variables=[
            var("x", "cell", "normal", (0, 1), "1 = 被形状覆盖"),
            var("o", "cell", "constant", doc="1=白圈 2=黑圈"),
        ],
        layers=[clue_circle("o", "圆圈"), shade()],
        rows=8, cols=8,
        notes="部分实现：五格骨牌 + 留白连通 + 圆圈。给出的形状目录未编码。",
        unencoded=["shapes"],
    )
    write_sample("statuepark", sample(
        "statuepark", 3, 3, title="3x3 一个 U",
        clues={"o": {"0,1": 2, "1,1": 1}},
    ))

    write_spec(
        "pentopia",
        variables=[
            var("x", "cell", "normal", (0, 1), "1 = 被覆盖"),
            var("a", "cell", "constant", doc="箭头位掩码 1上2下4左8右"),
        ],
        layers=[clue_number("a", "箭头掩码"), shade()],
        rows=8, cols=8,
        notes="部分实现：五格骨牌互不八邻接触 + 近视箭头。形状目录未编码。a 为方向位掩码。",
        unencoded=["shapes"],
    )
    write_sample("pentopia", sample(
        "pentopia", 3, 3, title="3x3 一个 U",
        clues={"a": {"2,1": 1}},
    ))

    write_spec(
        "pentatouch",
        variables=[
            var("x", "cell", "normal", (0, 1), "1 = 被覆盖"),
            var("o", "corner", "constant", doc="1 = 对角相接点"),
        ],
        layers=[
            layer("dot", "相接点", "dot", target="corner", role="input", var="o", palette={"1": BLACK}),
            shade(),
        ],
        rows=8, cols=8,
        notes="部分实现：五格骨牌 + 仅在标记格点对角相接。形状目录未编码。",
        unencoded=["shapes"],
    )
    write_sample("pentatouch", sample(
        "pentatouch", 2, 3, title="2x3 一个 U",
        clues={"o": {}},
    ))

    write_spec(
        "kissing",
        variables=[
            var("x", "cell", "normal", (0, 1), "1 = 被覆盖"),
            CC,
            var("k", "edge", "constant", doc="1 = 亲吻边"),
            var("w", "cell", "constant", doc="1 = × 禁入"),
        ],
        layers=[
            layer("kiss", "亲吻边", "edgeline", target="edge", role="input", var="k"),
            layer("block", "禁入", "cross", role="input", var="w"),
            shade(),
            partition_layer(),
        ],
        rows=8, cols=8,
        notes="部分实现：仅在标记边上正交相接，× 不覆盖。形状目录未编码。",
        unencoded=["shapes"],
    )
    write_sample("kissing", sample(
        "kissing", 1, 2, title="1x2 一吻",
        clues={"k": {"V,0,1": 1}, "w": {}},
    ))

    write_spec(
        "pencils",
        variables=[
            CC,
            var("k", "cell", "normal", (0, 2), "0=笔杆 1=笔头 2=笔迹"),
            var("n", "cell", "constant", doc="笔杆长度"),
        ],
        layers=[
            clue_number("n", "笔杆长"),
            layer(
                "kind", "笔的部件", "shade", role="output", var="k",
                palette={"0": "#f5d76e", "1": "#c0392b", "2": "#2980b9"},
            ),
            partition_layer(),
        ],
        rows=8, cols=8,
        notes="k: 0=笔杆 1=笔头 2=笔迹。",
    )
    write_sample("pencils", sample(
        "pencils", 1, 3, title="1x3 一支笔",
        clues={"n": {"0,0": 1}},
    ))

    write_spec(
        "tren",
        variables=[CC, var("n", "cell", "constant", doc="可滑动格数")],
        layers=[clue_number("n", "滑动格数"), partition_layer()],
        rows=8, cols=8,
    )
    write_sample("tren", sample(
        "tren", 1, 3, title="1x3 一辆车",
        clues={"n": {"0,1": 0}},
    ))

    write_spec(
        "kinkonkan",
        variables=[var("m", "cell", "normal", (0, 2), "0=无 1=\\\\ 2=/")],
        layers=[
            region_layer(),
            outside_layer("letters", "字母", param="letters", sides=("top", "bottom", "left", "right"), mode="int"),
            outside_layer("bounces", "反射次数", param="bounces", sides=("top", "bottom", "left", "right")),
            layer(
                "mirrors", "镜子", "shade", role="output", var="m",
                palette={"1": "#7f8ea3", "2": "#c0392b"},
            ),
        ],
        rows=8, cols=8, uses_regions=True,
        params={"defaults": {"letters": [], "bounces": [], "top": [], "bottom": [], "left": [], "right": []}},
        notes="部分实现：每区恰一面镜子。字母光束配对与反射次数未编码。m: 1=\\ 2=/。",
        unencoded=["letters", "bounces"],
    )
    write_sample("kinkonkan", sample(
        "kinkonkan", 2, 2, title="2x2 一面镜子",
        regions=block_regions(2, 2, 2, 2),
        params={"left": [-1, -1], "right": [-1, -1], "top": [-1, -1], "bottom": [-1, -1]},
    ))

    write_spec(
        "moonlight",
        variables=[
            var("x", "cell", "normal", (0, 2), "0=空 1=星 2=云"),
            var("o", "cell", "constant", doc="2 = 行星"),
            var("w", "cell", "constant", doc="1 = ×"),
        ],
        layers=[
            outside_layer("outside", "星/云个数", sides=("top", "bottom", "left", "right")),
            clue_circle("o", "行星"),
            layer("block", "禁入", "cross", role="input", var="w"),
            layer(
                "shapes", "星/云", "star", role="output", var="x",
                palette={"1": "#f1c40f", "2": "#7f8ea3"},
            ),
        ],
        rows=8, cols=8,
        params={"defaults": {"top": [], "bottom": [], "left": [], "right": []}},
        notes="部分实现：left/top=星数，right/bottom=云数；行星与×不放图。照明象限未编码。",
        unencoded=["light"],
    )
    write_sample("moonlight", sample(
        "moonlight", 2, 2, title="2x2 空盘",
        clues={"o": {}, "w": {}},
        params={"left": [0, 0], "top": [0, 0], "right": [0, 0], "bottom": [0, 0]},
    ))

    # ---- 分区 ----------------------------------------------------------------
    write_spec(
        "pentominous",
        variables=[CC, var("s", "cell", "constant", doc="形状字母 F=1 … Z=12")],
        layers=[
            layer("letter", "形状", "number", role="input", var="s", min=1, max=12),
            partition_layer(),
        ],
        rows=8, cols=8,
        notes="s: F=1 I=2 L=3 N=4 P=5 T=6 U=7 V=8 W=9 X=10 Y=11 Z=12。",
    )
    write_sample("pentominous", sample(
        "pentominous", 1, 5, title="1x5 一条 I",
        clues={"s": {"0,0": 2}},
    ))

    write_spec(
        "tetrominous",
        variables=[CC, var("s", "cell", "constant", doc="形状 I=1 O=2 T=3 L=4 S=5")],
        layers=[
            layer("letter", "形状", "number", role="input", var="s", min=1, max=5),
            partition_layer(),
        ],
        rows=8, cols=8,
        notes="s: I=1 O=2 T=3 L=4 S=5（自由四格骨牌，含镜像）。",
    )
    write_sample("tetrominous", sample(
        "tetrominous", 2, 2, title="2x2 一个 O",
        clues={"s": {"0,0": 2}},
    ))

    write_spec(
        "heteromino",
        variables=[CC],
        layers=[partition_layer()],
        rows=8, cols=8,
        notes="相邻三格骨牌的平移类（I 横/竖 + L 四朝向）必须不同。",
    )
    write_sample("heteromino", sample(
        "heteromino", 1, 3, title="1x3 一条 I",
        clues={},
    ))

    write_spec(
        "cbblock",
        variables=[CC],
        layers=[region_layer("虚线块"), partition_layer()],
        rows=8, cols=8, uses_regions=True,
        notes="给定区域是虚线描边的块；求解分区每区恰好两块，非矩形，相邻不全等。",
    )
    write_sample("cbblock", sample(
        "cbblock", 3, 3, title="3x3 两区",
        regions={
            "0,0": 0, "0,1": 0, "0,2": 0,
            "1,0": 1, "1,1": 1,
            "1,2": 2,
            "2,0": 3, "2,1": 3, "2,2": 3,
        },
    ))

    write_spec(
        "slashpack",
        variables=[
            var("s", "cell", "normal", (0, 2), "0=无 1=\\\\ 2=/"),
            var("u", "cell", "normal", (0, 63), "三角区域号 A"),
            var("v", "cell", "normal", (0, 63), "三角区域号 B"),
            var("n", "cell", "constant", doc="数字"),
        ],
        layers=[
            clue_number("n", "数字"),
            layer(
                "slash", "斜线", "shade", role="output", var="s",
                palette={"1": GRAY, "2": "#c0392b"},
            ),
        ],
        rows=8, cols=8,
        notes="部分实现：三角邻边编号一致 + 每区 1..N 各一次。s: 1=\\ 2=/。",
        unencoded=["connectivity"],
    )
    write_sample("slashpack", sample(
        "slashpack", 1, 2, title="1x2 一区",
        clues={"n": {"0,0": 1, "0,1": 2}},
    ))

    write_spec(
        "symmarea",
        variables=[CC, var("n", "cell", "constant", doc="区域面积")],
        layers=[clue_number("n", "面积"), partition_layer()],
        rows=8, cols=8,
        notes="每区 180° 对称，中心可为格心、边心或顶点。",
    )
    write_sample("symmarea", sample(
        "symmarea", 2, 2, title="2x2 一块",
        clues={"n": {"0,0": 4}},
    ))

    write_spec(
        "subomino",
        variables=[CC, var("n", "cell", "constant", doc="区域面积")],
        layers=[clue_number("n", "面积"), partition_layer()],
        rows=8, cols=8,
    )
    write_sample("subomino", sample(
        "subomino", 2, 2, title="2x2 一块",
        clues={"n": {"0,0": 4}},
    ))

    write_spec(
        "mirrorbk",
        variables=[
            CC,
            var("n", "cell", "constant", doc="区域面积"),
            var("m", "edge", "constant", doc="1 = 镜子"),
        ],
        layers=[
            clue_number("n", "面积"),
            layer("mirror", "镜子", "edgeline", target="edge", role="input", var="m"),
            partition_layer(),
        ],
        rows=8, cols=8,
        notes="镜子两侧两区关于该格线轴对称。",
    )
    write_sample("mirrorbk", sample(
        "mirrorbk", 2, 2, title="2x2 一面镜子",
        clues={"n": {"0,0": 2, "0,1": 2}, "m": {"V,0,1": 1, "V,1,1": 1}},
    ))

    write_spec(
        "nikoji",
        variables=[CC, var("s", "cell", "constant", doc="字母编号")],
        layers=[
            layer("letter", "字母", "number", role="input", var="s", min=1),
            partition_layer(),
        ],
        rows=8, cols=8,
        notes="同字母平移全等（含字母位置）；异字母任意旋转翻转都不全等。",
    )
    write_sample("nikoji", sample(
        "nikoji", 2, 2, title="2x2 两竖",
        clues={"s": {"0,0": 1, "0,1": 1}},
    ))

    write_spec(
        "dbchoco",
        variables=[
            CC,
            var("g", "cell", "constant", doc="1=灰 0=白", dense=True),
            var("n", "cell", "constant", doc="一组面积"),
        ],
        layers=[
            shade("g", "灰色", role="input"),
            clue_number("n", "一组面积"),
            partition_layer(),
        ],
        rows=8, cols=8,
        notes="部分实现：灰白两块等面积、各自边数足够连通、且相邻。灰白全等（旋转翻转）未编码。",
        unencoded=["congruence"],
    )
    write_sample("dbchoco", sample(
        "dbchoco", 2, 2, title="2x2 一对",
        clues={"g": from_grid("1 0\n1 0"), "n": {"0,0": 2}},
    ))

    write_spec(
        "sendai",
        variables=[CC, var("n", "cell", "constant", doc="市的个数")],
        layers=[region_layer("县"), clue_number("n", "市数"), partition_layer()],
        rows=8, cols=8, uses_regions=True,
        notes="每市须与另一个平移全等的市相邻。数字=该县的市数。",
    )
    write_sample("sendai", sample(
        "sendai", 2, 2, title="2x2 两市",
        regions=block_regions(2, 2, 2, 2),
        clues={"n": {"0,0": 2}},
    ))

    write_spec(
        "lohkous",
        variables=[
            CC,
            var("n1", "cell", "constant", doc="段长 1"),
            var("n2", "cell", "constant", doc="段长 2"),
            var("n3", "cell", "constant", doc="段长 3"),
        ],
        layers=[
            layer("n1", "段长1", "number", role="input", var="n1", min=0),
            layer("n2", "段长2", "number", role="input", var="n2", min=0),
            layer("n3", "段长3", "number", role="input", var="n3", min=0),
            partition_layer(),
        ],
        rows=8, cols=8,
        notes="一格可写最多三个不重复段长，等于该区所有横纵段长的集合。",
    )
    write_sample("lohkous", sample(
        "lohkous", 2, 2, title="2x2 一段长",
        clues={"n1": {"0,0": 2}},
    ))

    write_spec(
        "narrow",
        variables=[CC, var("s", "cell", "constant", doc="符号")],
        layers=[
            layer("symbol", "符号", "number", role="input", var="s", min=1),
            partition_layer(),
        ],
        rows=8, cols=8,
        notes="非矩形；同符号不同形（自由全等）；禁止同符号 2×2。",
    )
    write_sample("narrow", sample(
        "narrow", 2, 3, title="2x3 两个 L",
        clues={"s": {"0,0": 1, "0,2": 2}},
    ))

    write_spec(
        "voxas",
        variables=[
            CC,
            var("o", "edge", "constant", doc="1白 2黑 3灰"),
        ],
        layers=[
            layer(
                "dot", "圆点", "circle", target="edge", role="input", var="o",
                palette={"1": WHITE, "2": BLACK, "3": GRAY},
            ),
            partition_layer(),
        ],
        rows=8, cols=8,
        notes="o: 1=白(面积朝向都同) 2=黑(都不同) 3=灰(恰一个相同)。",
    )
    write_sample("voxas", sample(
        "voxas", 2, 2, title="2x2 两横",
        clues={"o": {"H,1,0": 1}},
    ))

    write_spec(
        "heavydots",
        variables=[
            CC,
            var("n", "cell", "constant", doc="区域面积"),
            var("o", "corner", "constant", doc="1=白点四界 2=黑点三界"),
        ],
        layers=[
            clue_number("n", "面积"),
            layer(
                "dot", "顶点", "dot", target="corner", role="input", var="o",
                palette={"1": WHITE, "2": BLACK},
            ),
            partition_layer(),
        ],
        rows=8, cols=8,
        notes="o: 1=白(恰四条界) 2=黑(恰三条界)。与已标点相邻的未标点不能为 3/4 条。",
    )
    write_sample("heavydots", sample(
        "heavydots", 2, 2, title="2x2 两横",
        clues={"n": {"0,0": 2, "1,0": 2}, "o": {}},
    ))


if __name__ == "__main__":
    _write()
    print("wrote 放置/分区 specs and samples")
