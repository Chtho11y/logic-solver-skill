"""Write spec JSON + samples for remaining 填写 rules."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tools.scaffold import (  # noqa: E402
    BLACK,
    WHITE,
    LOOP_VAR,
    answer_number,
    clue_arrow,
    clue_circle,
    clue_number,
    layer,
    link_layer,
    outside_layer,
    region_layer,
    sample,
    shade,
    var,
    write_sample,
    write_spec,
)
from tools.samples import block_regions, from_grid, row_regions  # noqa: E402

X = var("x", "cell", "normal", (0, 20), "填数（0=空/黑）")
X1 = var("x", "cell", "normal", (1, 12), "1..N")
A = var("a", "cell", "normal", (0, 8), "箭头 0-3，8=无")
G = var("g", "cell", "normal", (1, 2), "1=╲ 2=╱")
N = var("n", "cell", "constant", doc="数字提示")
O = var("o", "cell", "constant", doc="1=白圈 2=黑圈")
D = var("d", "cell", "constant", doc="箭头方向")
B = var("b", "cell", "constant", doc="1=黑格/墙")
M = var("m", "cell", "constant", doc="1=叉/禁止填数")
F = var("f", "cell", "normal", (0, 1), "1=已填")
DEST = var("dest", "cell", "normal", (0, 80), "箭头终点编号")
DIST = var("dist", "cell", "normal", (0, 80), "到目标的距离")
PAR = var("par", "corner", "normal", (0, 4), "斜线森林父方向")
RK = var("rk", "corner", "normal", (0, 80), "斜线森林序")
EDGE_O = var("o", "edge", "constant", doc="1=白点 2=黑点")
CORNER_O = var("o", "corner", "constant", doc="1=白点 2=黑点")
CORNER_N = var("n", "corner", "constant", doc="顶点斜线数")
HCLUE = var("h", "cell", "constant", doc="横向和")
VCLUE = var("v", "cell", "constant", doc="纵向和")
E = LOOP_VAR


def unit_regions(rows: int, cols: int) -> dict[str, int]:
    return {f"{r},{c}": r * cols + c for r in range(rows) for c in range(cols)}


def _write():
    write_spec(
        "bosanowa",
        variables=[X, O],
        layers=[clue_circle("o", "填数圆圈"), answer_number()],
        rows=8, cols=8,
        notes="仅在圆圈格填正整数；x=与横竖相邻填数之差的绝对值之和。",
    )
    write_sample("bosanowa", sample(
        "bosanowa", 1, 3, title="1x3 邻差和",
        clues={"o": {"0,0": 1, "0,1": 1, "0,2": 1}},
    ))

    write_spec(
        "gokigen",
        variables=[G, CORNER_N, PAR, RK],
        layers=[
            layer("clue", "顶点数字", "number", target="corner", var="n", min=0, max=4),
            layer("diag", "斜线", "diagonal", role="output", var="g"),
        ],
        rows=8, cols=8,
        notes="g: 1=╲ 2=╱。par/rk 为无环森林辅助量。",
    )
    write_sample("gokigen", sample(
        "gokigen", 2, 2, title="2x2 斜线迷宫",
        clues={"n": {"1,1": 2}},
    ))

    write_spec(
        "simplegako",
        variables=[X1],
        layers=[layer("given", "已给数字", "number", var="x", min=1), answer_number()],
        rows=8, cols=8,
        notes="每格数字=该数字在其所在行+列出现次数（含自身）。",
    )
    write_sample("simplegako", sample(
        "simplegako", 2, 2, title="2x2 简单计数",
        clues={"x": {}},
    ))

    write_spec(
        "blind",
        variables=[A],
        layers=[region_layer(), layer("answer", "箭头", "arrow", role="output", var="a")],
        rows=8, cols=8, uses_regions=True,
        notes="每区一箭头；每行每列↑↓←→各一次。8=无箭头。",
    )
    write_sample("blind", sample(
        "blind", 4, 4, title="4x4 盲点",
        regions=unit_regions(4, 4),
    ))

    write_spec(
        "fuzuli",
        variables=[X, M],
        layers=[
            layer("forbid", "叉号", "cross", var="m"),
            answer_number(),
        ],
        rows=8, cols=8,
        notes="values 为可填数字列表；每行每列各出现一次；无全填 2x2；叉格不填。",
        params={"defaults": {"values": [1, 2]}},
    )
    write_sample("fuzuli", sample(
        "fuzuli", 4, 4, title="4x4 冗余",
        clues={"m": {"0,3": 1, "3,0": 1}},
        params={"values": [1, 2]},
    ))

    write_spec(
        "doppelblock",
        variables=[X],
        layers=[
            outside_layer(label="黑格间数字和", sides=("top", "left")),
            answer_number(),
        ],
        rows=8, cols=8,
        notes="0=黑格，每行每列两个；其余为 1..N-2 各一次。盘外=两黑格之间的和。",
    )
    write_sample("doppelblock", sample(
        "doppelblock", 4, 4, title="4x4 双黑格",
        params={"left": [3, 0, 0, 3], "top": [3, 0, 0, 3]},
    ))

    write_spec(
        "renban",
        variables=[X1],
        layers=[region_layer(), layer("given", "已给数字", "number", var="x", min=1), answer_number()],
        rows=8, cols=8, uses_regions=True,
        notes="区域内连续；跨粗边框相邻两数之差=该段公共边界长度。",
    )
    write_sample("renban", sample(
        "renban", 2, 4, title="2x4 连番窗口",
        regions=block_regions(2, 4, 2, 2),
        clues={"x": {"0,0": 1, "1,3": 4}},
    ))

    write_spec(
        "goishi",
        variables=[X, O],
        layers=[clue_circle("o", "棋子"), answer_number()],
        rows=8, cols=8,
        notes="圆圈为棋子；x 为捡取顺序 1..K。",
    )
    write_sample("goishi", sample(
        "goishi", 2, 2, title="L 形三子",
        clues={"o": {"0,0": 2, "0,1": 2, "1,0": 2}},
    ))

    write_spec(
        "kakuro",
        variables=[X, B, HCLUE, VCLUE],
        layers=[
            shade("b", "黑格", role="input"),
            clue_number("h", "横向和"),
            layer("vclue", "纵向和", "number", var="v", min=0),
            answer_number(),
        ],
        rows=8, cols=8,
        notes="白格填 1-9；h/v 写在黑格上，分别约束其右方横段 / 下方纵段。",
    )
    write_sample("kakuro", sample(
        "kakuro", 3, 3, title="2x2 数和",
        clues={
            "b": {"0,0": 1, "0,1": 1, "0,2": 1, "1,0": 1, "2,0": 1},
            "h": {"1,0": 3, "2,0": 4},
            "v": {"0,1": 4, "0,2": 3},
        },
    ))

    write_spec(
        "easyasabc",
        variables=[X],
        layers=[
            outside_layer(label="第一字符", sides=("top", "bottom", "left", "right")),
            answer_number(),
        ],
        rows=8, cols=8,
        notes="x: 1=A,2=B,…,0=空。values 为字母编号。盘外=该方向见到的第一个字母。",
        params={"defaults": {"values": [1, 2]}},
    )
    write_sample("easyasabc", sample(
        "easyasabc", 3, 3, title="3x3 简单字符",
        params={
            "values": [1, 2],
            "left": [1, 2, 1],
            "top": [1, 2, 1],
            "right": [2, 1, 2],
            "bottom": [2, 1, 2],
        },
    ))

    write_spec(
        "hanare",
        variables=[X],
        layers=[region_layer(), answer_number()],
        rows=8, cols=8, uses_regions=True,
        notes="每区一格填面积。同行/列且中间无其他数字时，中间空格数=两数之差。",
    )
    write_sample("hanare", sample(
        "hanare", 3, 3, title="3x3 差距一致",
        regions=block_regions(3, 3, 1, 3),
    ))

    write_spec(
        "r",
        variables=[X1],
        layers=[region_layer(), layer("given", "已给数字", "number", var="x", min=1), answer_number()],
        rows=8, cols=8, uses_regions=True,
        notes="拉丁方 1..N；每个区域内数字构成连续段。",
    )
    write_sample("r", sample(
        "r", 4, 4, title="4x4 连番",
        regions=block_regions(4, 4, 2, 2),
        clues={"x": {"0,0": 1, "0,3": 4}},
    ))

    write_spec(
        "roma",
        variables=[A, O, DIST],
        layers=[
            region_layer(),
            clue_circle("o", "黑圈"),
            layer("answer", "箭头", "arrow", role="output", var="a"),
        ],
        rows=8, cols=8, uses_regions=True,
        notes="每区箭头互异。沿箭头必达黑圈。dist 为辅助距离。",
    )
    write_sample("roma", sample(
        "roma", 2, 2, title="2x2 罗马",
        regions=unit_regions(2, 2),
        clues={"o": {"1,1": 2}},
    ))

    write_spec(
        "toichika",
        variables=[A],
        layers=[region_layer(), layer("answer", "箭头", "arrow", role="output", var="a")],
        rows=8, cols=8, uses_regions=True,
        notes="每区一箭头；箭头两两对射且中间无箭头；配对两区无公共边界。8=无。",
    )
    write_sample("toichika", sample(
        "toichika", 4, 4, title="4x4 山盟海誓",
        regions=row_regions(4, 4),
    ))

    write_spec(
        "japanesesums",
        variables=[X],
        layers=[
            outside_layer(label="段和", sides=("top", "left")),
            answer_number(),
        ],
        rows=8, cols=8,
        notes="values 为可填数字；每行每列至多一次。盘外依次为各填数段之和，? 为未知和。",
        params={"defaults": {"values": [1, 2]}},
    )
    write_sample("japanesesums", sample(
        "japanesesums", 3, 3, title="3x3 日本和",
        params={
            "values": [1, 2],
            "left": [3, [2, 1], 3],
            "top": [3, [2, 1], 3],
        },
    ))

    write_spec(
        "wagiri",
        variables=[G, CORNER_N, M],
        layers=[
            layer("clue", "顶点数字", "number", target="corner", var="n", min=0, max=4),
            layer("mark", "輪/切", "text", var="m"),
            layer("diag", "斜线", "diagonal", role="output", var="g"),
        ],
        rows=8, cols=8,
        notes="g: 1=╲ 2=╱。m: 1=輪 2=切（是否在环上）当前未编码。",
        unencoded=["m"],
    )
    write_sample("wagiri", sample(
        "wagiri", 2, 2, title="2x2 斜线(环和切)",
        clues={"n": {"1,1": 2}},
    ))

    write_spec(
        "makaro",
        variables=[X, B, D],
        layers=[
            region_layer(),
            shade("b", "黑格", role="input"),
            clue_arrow("d", "极大箭头"),
            answer_number(),
        ],
        rows=8, cols=8, uses_regions=True,
        notes="白格区域 1..N；相邻不同。黑格箭头指向邻接数字中唯一最大者。",
    )
    write_sample("makaro", sample(
        "makaro", 2, 2, title="2x2 极大箭头",
        regions={"0,0": 0, "0,1": 0, "1,0": 0, "1,1": 0},
        clues={"b": {"0,0": 1}, "d": {"0,0": 3}},
    ))

    write_spec(
        "yajirushi",
        variables=[A],
        layers=[layer("answer", "箭头", "arrow", role="output", var="a")],
        rows=8, cols=8,
        notes="箭头两两对射、中间无箭头且不相邻；所有空格都在某对箭头之间。8=无。",
    )
    write_sample("yajirushi", sample(
        "yajirushi", 3, 3, title="3x3 yajirushi",
        clues={"a": {}},
    ))

    write_spec(
        "cojun",
        variables=[X1],
        layers=[region_layer(), layer("given", "已给数字", "number", var="x", min=1), answer_number()],
        rows=8, cols=8, uses_regions=True,
        notes="区域 1..N；相邻不同；同区纵向相邻则上格大于下格。",
    )
    write_sample("cojun", sample(
        "cojun", 4, 4, title="4x4 叠叠高",
        regions=block_regions(4, 4, 2, 2),
        clues={"x": {"0,0": 3}},
    ))

    write_spec(
        "tateyoko",
        variables=[var("x", "cell", "normal", (0, 2), "0=黑 1=横 2=竖"), B, N],
        layers=[
            shade("b", "黑格", role="input"),
            clue_number(),
            layer("answer", "横竖", "number", role="output", var="x"),
        ],
        rows=8, cols=8,
        notes="白格 1=横线 2=竖线。白数字=线段长；黑数字=引出线段数。一线段至多一个白数字。",
    )
    write_sample("tateyoko", sample(
        "tateyoko", 2, 3, title="2x3 翠竹交错",
        clues={"n": {"0,0": 3, "1,2": 3}},
    ))

    write_spec(
        "arrowflow",
        variables=[A, N, DEST],
        layers=[clue_number(), layer("answer", "箭头", "arrow", role="output", var="a")],
        rows=8, cols=8,
        notes="空格放箭头，相同箭头不相邻。沿箭头到达线索格。n=到达该格的箭头格数，-1=问号。dest 为辅助。",
    )
    write_sample("arrowflow", sample(
        "arrowflow", 3, 3, title="3x3 箭头流动",
        clues={"n": {"1,1": 8}},
    ))

    write_spec(
        "scrabble",
        variables=[X, F],
        layers=[layer("given", "已给字母", "number", var="x", min=0), answer_number()],
        rows=8, cols=8,
        notes="x: 1=A,2=B,…,0=空。param words 为单词（字母编号列表），每个恰好出现一次。",
        params={"defaults": {"words": []}},
    )
    write_sample("scrabble", sample(
        "scrabble", 1, 3, title="CAT",
        clues={"x": {"0,0": 3, "0,2": 20}},
        params={"words": [[3, 1, 20]]},
    ))

    write_spec(
        "kropki-pairs",
        variables=[X1, EDGE_O],
        layers=[
            layer("dot", "黑白点", "dot", target="edge", var="o"),
            layer("given", "已给数字", "number", var="x", min=1),
            answer_number(),
        ],
        rows=8, cols=8,
        notes="拉丁方。白点差 1，黑点比 1:2。未给出的点不约束。",
    )
    write_sample("kropki-pairs", sample(
        "kropki-pairs", 3, 3, title="3x3 黑白点对",
        clues={"o": {"V,0,1": 1, "H,1,0": 2}, "x": {"0,0": 1}},
    ))

    write_spec(
        "skyscrapers",
        variables=[X1],
        layers=[
            outside_layer(label="可见楼数", sides=("top", "bottom", "left", "right")),
            layer("given", "已给数字", "number", var="x", min=1),
            answer_number(),
        ],
        rows=8, cols=8,
        notes="默认拉丁方 1..N。盘外=该方向能看到的摩天楼个数。",
    )
    write_sample("skyscrapers", sample(
        "skyscrapers", 3, 3, title="3x3 摩天楼",
        params={"left": [3, 2, 1], "top": [3, 2, 1], "right": [1, 2, 2], "bottom": [1, 2, 2]},
    ))

    write_spec(
        "consecutiveq",
        variables=[X1, CORNER_O],
        layers=[
            layer("dot", "四角点", "dot", target="corner", var="o"),
            layer("given", "已给数字", "number", var="x", min=1),
            answer_number(),
        ],
        rows=8, cols=8,
        notes="拉丁方。白点=周围四数恰一对连续，黑点=至少两对。未给出的点不约束。",
    )
    write_sample("consecutiveq", sample(
        "consecutiveq", 3, 3, title="3x3 连续四数组",
        clues={"o": {"1,1": 2}, "x": {"0,0": 1}},
    ))

    write_spec(
        "snail",
        variables=[X, O, M],
        layers=[
            clue_circle("o", "起点"),
            layer("forbid", "叉号", "cross", var="m"),
            answer_number(),
        ],
        rows=8, cols=8,
        notes="1..K 每行每列各一次。从圆圈起沿螺旋，填数按 1..K 循环。叉格不填。",
        params={"defaults": {"values": [1, 2]}},
    )
    write_sample("snail", sample(
        "snail", 3, 3, title="3x3 蜗牛",
        clues={"o": {"0,0": 1}, "m": {"1,1": 1}},
        params={"values": [1, 2]},
    ))

    write_spec(
        "magic",
        variables=[X, M],
        layers=[
            outside_layer(label="多位数之和", sides=("top", "left")),
            layer("forbid", "叉号", "cross", var="m"),
            layer("given", "已给数码", "number", var="x", min=0),
            answer_number(),
        ],
        rows=8, cols=8,
        notes="数码列表每行每列各一次。盘外=连续数码组成的多位数之和。叉格不填。",
        params={"defaults": {"values": [1, 2]}},
    )
    write_sample("magic", sample(
        "magic", 3, 3, title="3x3 魔夏",
        params={"values": [1, 2], "left": [12, 3, 12], "top": [12, 3, 12]},
    ))

    write_spec(
        "kropki",
        variables=[X1, EDGE_O],
        layers=[
            layer("dot", "黑白点", "dot", target="edge", var="o"),
            layer("given", "已给数字", "number", var="x", min=1),
            answer_number(),
        ],
        rows=8, cols=8,
        notes="拉丁方。全部黑白点已给出。相邻 1 与 2 可用任一种点。",
    )
    write_sample("kropki", sample(
        "kropki", 2, 2, title="2x2 黑白点",
        clues={"o": {"V,0,1": 1, "V,1,1": 1, "H,1,0": 1, "H,1,1": 1}},
    ))

    write_spec(
        "hebi",
        variables=[X, F, B, N, D],
        layers=[
            shade("b", "黑格", role="input"),
            clue_number(),
            clue_arrow("d", "视线"),
            answer_number(),
        ],
        rows=8, cols=8,
        notes="蛇为 1-5 路径；蛇与蛇正交不相邻。箭头数字=该方向直到墙/边界的第一个数，0=没有。",
    )
    write_sample("hebi", sample(
        "hebi", 3, 5, title="一条蛇",
        clues={"n": {"0,4": 3}, "d": {"0,4": 2}},
    ))

    write_spec(
        "ubahn",
        variables=[E, B, N],
        layers=[
            shade("b", "黑格", role="input"),
            outside_layer(label="连接类型计数", sides=("top", "left")),
            link_layer(),
        ],
        rows=8, cols=8,
        notes="无线或度 2/3/4，无线死胡同。盘外若为四元组则计 [交叉,丁字,直行,转弯]。",
    )
    write_sample("ubahn", sample(
        "ubahn", 2, 2, title="2x2 环",
        clues={"b": {}},
    ))


if __name__ == "__main__":
    _write()
    print("wrote fill specs and samples")
