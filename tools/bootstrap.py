"""Regenerate the bundled ``impls/*.json`` specs from one compact table.

The DSL programs (``impls/*.dsl``) and sample instances are hand written; this
script only (re)creates the spec files so that every puzzle describes its
variables and drawing layers in exactly the same style::

    python -m tools.bootstrap
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.scaffold import (  # noqa: E402
    BLACK,
    WHITE,
    answer_number,
    clue_arrow,
    clue_circle,
    clue_number,
    edgeline_layer,
    layer,
    link_layer,
    outside_layer,
    partition_layer,
    region_layer,
    shade,
    var,
    write_spec,
)

SHADE = var("x", "cell", "normal", (0, 1), "0 = 留白, 1 = 涂黑")
NUM = var("n", "cell", "constant", None, "数字提示")


def cell_const(name: str, doc: str = "") -> dict:
    return var(name, "cell", "constant", None, doc)


# key -> (variables, layers, rows, cols, usesRegions, notes, params)
TABLE: dict[str, dict] = {
    # ---------------------------------------------------------------- 涂黑 I
    "nurikabe": dict(
        variables=[SHADE, NUM],
        layers=[clue_number("n", "岛屿数字"), shade()],
        rows=10, cols=10,
    ),
    "hitori": dict(
        variables=[SHADE, var("n", "cell", "constant", None, "盘面数字", dense=True)],
        layers=[clue_number("n", "盘面数字"), shade()],
        rows=8, cols=8,
    ),
    "heyawake": dict(
        variables=[SHADE, NUM],
        layers=[region_layer(), clue_number("n", "区域黑格数"), shade()],
        rows=10, cols=10, uses_regions=True,
    ),
    "lits": dict(
        variables=[SHADE, var("t", "cell", "normal", (0, 3), "骨牌形状 0=I 1=L 2=S 3=T")],
        layers=[region_layer(), shade()],
        rows=10, cols=10, uses_regions=True,
        notes="t 为每个区域四格骨牌的形状编号，用于判定相邻区域是否全等。",
    ),
    "aqre": dict(
        variables=[SHADE, NUM],
        layers=[region_layer(), clue_number("n", "区域黑格数"), shade()],
        rows=10, cols=10, uses_regions=True,
    ),
    "kurodoko": dict(
        variables=[SHADE, NUM],
        layers=[clue_number("n", "可见留白格数"), shade()],
        rows=9, cols=9,
    ),
    "canal": dict(
        variables=[SHADE, NUM],
        layers=[clue_number("n", "可见涂黑格数"), shade()],
        rows=9, cols=9,
    ),
    "creek": dict(
        variables=[SHADE, var("n", "corner", "constant", None, "顶点周围黑格数")],
        layers=[
            layer("clue", "顶点数字", "number", target="corner", role="input", var="n", min=0, max=4),
            shade(),
        ],
        rows=8, cols=8,
        notes="提示写在格点 (corner) 上，取值 0-4。",
    ),
    "nurimisaki": dict(
        variables=[SHADE, NUM],
        layers=[clue_number("n", "岬圆圈 (0 = 无数字)"), shade()],
        rows=9, cols=9,
        notes="每个提示格都是一个圆圈；数字 0 表示圆圈内没有写数。",
    ),
    "cave": dict(
        variables=[SHADE, NUM],
        layers=[clue_number("n", "可见留白格数"), shade()],
        rows=9, cols=9,
    ),
    "aquapelago": dict(
        variables=[SHADE, NUM],
        layers=[clue_number("n", "岛屿格数"), shade()],
        rows=9, cols=9,
    ),
    "context": dict(
        variables=[SHADE, NUM],
        layers=[clue_number("n", "邻接/接触黑格数"), shade()],
        rows=9, cols=9,
    ),
    "paintarea": dict(
        variables=[SHADE, NUM],
        layers=[region_layer(), clue_number("n", "相邻黑格数"), shade()],
        rows=9, cols=9, uses_regions=True,
    ),
    # --------------------------------------------------------------- 涂黑 II
    "norinori": dict(
        variables=[SHADE],
        layers=[region_layer(), shade("x", "海苔")],
        rows=8, cols=8, uses_regions=True,
    ),
    "chocona": dict(
        variables=[SHADE, NUM],
        layers=[region_layer(), clue_number("n", "区域黑格数"), shade()],
        rows=9, cols=9, uses_regions=True,
    ),
    "yinyang": dict(
        variables=[
            var("x", "cell", "normal", (0, 1), "0 = 白圈, 1 = 黑圈"),
            cell_const("g", "已给出的圆圈 (0 = 白, 1 = 黑)"),
        ],
        layers=[
            layer("given", "已给圆圈", "circle", role="input", var="g",
                  palette={"0": WHITE, "1": BLACK}),
            layer("answer", "阴阳", "circle", role="output", var="x",
                  palette={"0": WHITE, "1": BLACK}),
        ],
        rows=9, cols=9,
    ),
    "box": dict(
        variables=[SHADE],
        layers=[
            outside_layer("outside", "行/列加权和", param="outside", sides=("top", "left")),
            shade(),
        ],
        rows=7, cols=7,
        params={"defaults": {"top": [], "left": []}},
        notes="left[r] = 该行涂黑格的列号之和；top[c] = 该列涂黑格的行号之和（均从 1 开始）。",
    ),
    "tilepaint": dict(
        variables=[SHADE],
        layers=[
            region_layer(),
            outside_layer("outside", "行/列黑格数", param="outside", sides=("top", "left")),
            shade(),
        ],
        rows=8, cols=8, uses_regions=True,
        params={"defaults": {"top": [], "left": []}},
    ),
    "cbanana": dict(
        variables=[SHADE, NUM],
        layers=[clue_number("n", "连通组面积"), shade()],
        rows=6, cols=6,
    ),
    "lightshadow": dict(
        variables=[
            var("x", "cell", "normal", (0, 1), "0 = 涂白, 1 = 涂黑"),
            cell_const("bn", "黑数字"),
            cell_const("wn", "白数字"),
        ],
        layers=[
            layer("black", "黑数字", "number", role="input", var="bn", palette={"*": BLACK}),
            layer("white", "白数字", "number", role="input", var="wn", palette={"*": "#2b6cb0"}),
            shade(),
        ],
        rows=9, cols=9,
    ),
    "mochikoro": dict(
        variables=[SHADE, NUM],
        layers=[clue_number("n", "留白矩形面积"), shade()],
        rows=8, cols=8,
    ),
    # -------------------------------------------------------------- 涂黑 III
    "kurotto": dict(
        variables=[SHADE, NUM],
        layers=[clue_number("n", "相邻黑块总面积"), shade()],
        rows=8, cols=8,
        notes="数字 -1 表示圆圈内没有写数（不提供信息）。",
    ),
    "mines": dict(
        variables=[
            var("x", "cell", "normal", (0, 1), "1 = 地雷"),
            cell_const("n", "周围八格雷数"),
        ],
        layers=[clue_number("n", "雷数"), layer("mine", "地雷", "circle", role="output",
                                                var="x", palette={"1": BLACK})],
        rows=8, cols=8,
    ),
    "nonogram": dict(
        variables=[SHADE],
        layers=[
            outside_layer("outside", "行列段长", param="outside",
                          sides=("top", "left"), mode="list"),
            shade(),
        ],
        rows=10, cols=10,
        params={"defaults": {"top": [], "left": []}},
    ),
    "starbattle": dict(
        variables=[var("x", "cell", "normal", (0, 1), "1 = 星")],
        layers=[
            region_layer(),
            layer("star", "星", "star", role="output", var="x"),
        ],
        rows=8, cols=8, uses_regions=True,
        params={"defaults": {"stars": 1}},
        notes="params.stars 为每行/列/区域的星数。",
    ),
    "shimaguni": dict(
        variables=[SHADE, NUM],
        layers=[region_layer(), clue_number("n", "区域黑格数"), shade()],
        rows=9, cols=9, uses_regions=True,
    ),
    "tents": dict(
        variables=[
            var("x", "cell", "normal", (0, 1), "1 = 帐篷"),
            var("a", "cell", "normal", (0, 4), "帐篷配对的树方向 0=无 1=上 2=下 3=左 4=右"),
            cell_const("t", "树 (值 1)"),
        ],
        layers=[
            layer("tree", "树", "tree", role="input", var="t"),
            outside_layer("outside", "行/列帐篷数", param="outside", sides=("top", "left")),
            layer("tent", "帐篷", "tent", role="output", var="x"),
        ],
        rows=8, cols=8,
        params={"defaults": {"top": [], "left": []}},
    ),
    "akari": dict(
        variables=[
            var("x", "cell", "normal", (0, 1), "1 = 灯泡"),
            cell_const("w", "黑格 (1 = 无数字黑格)"),
            cell_const("n", "黑格数字"),
        ],
        layers=[
            layer("wall", "黑格", "shade", role="input", var="w", palette={"1": BLACK}),
            layer("clue", "黑格数字", "number", role="input", var="n",
                  palette={"*": "#ffffff"}),
            layer("bulb", "灯泡", "bulb", role="output", var="x"),
        ],
        rows=8, cols=8,
        notes="每个有数字的黑格同时要在 w 中标记为 1。",
    ),
    "battleship": dict(
        variables=[
            var("x", "cell", "normal", (0, 6),
                "0=水 1=单格船 2=船身 3=头朝上 4=头朝下 5=头朝左 6=头朝右"),
            cell_const("g", "已给船部分 (同 x 编码)"),
            cell_const("w", "1 = 水波 (禁船)"),
        ],
        layers=[
            layer("given", "已给船部", "ship", role="input", var="g"),
            layer("wave", "水波", "wave", role="input", var="w"),
            outside_layer("outside", "行/列船格数", param="outside", sides=("top", "left")),
            layer("ship", "舰队", "ship", role="output", var="x"),
        ],
        rows=8, cols=8,
        params={"defaults": {"top": [], "left": [], "fleet": [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]}},
        notes="后端求解器待实现；当前仅供前端编辑与展示。",
    ),
    # ----------------------------------------------------------------- 填写
    "sudoku": dict(
        variables=[var("x", "cell", "normal", (1, 9), "1-9")],
        layers=[
            layer("given", "已给数字", "number", role="input", var="x", min=1, max=9),
            answer_number("x", "解"),
        ],
        rows=9, cols=9,
    ),
    "suguru": dict(
        variables=[var("x", "cell", "normal", (1, 9))],
        layers=[
            region_layer(),
            layer("given", "已给数字", "number", role="input", var="x", min=1, max=9),
            answer_number("x", "解"),
        ],
        rows=6, cols=6, uses_regions=True,
    ),
    "ripple": dict(
        variables=[var("x", "cell", "normal", (1, 9))],
        layers=[
            region_layer(),
            layer("given", "已给数字", "number", role="input", var="x", min=1, max=9),
            answer_number("x", "解"),
        ],
        rows=6, cols=6, uses_regions=True,
    ),
    "putteria": dict(
        variables=[var("x", "cell", "normal", (0, 12), "0 = 空格")],
        layers=[region_layer(), answer_number("x", "填数")],
        rows=7, cols=7, uses_regions=True,
    ),
    "sukoro": dict(
        variables=[
            var("x", "cell", "normal", (0, 4), "0 = 空格"),
            var("f", "cell", "normal", (0, 1), "1 = 该格填了数"),
        ],
        layers=[
            layer("given", "已给数字", "number", role="input", var="x", min=0, max=4),
            answer_number("x", "填数"),
        ],
        rows=6, cols=6,
    ),
    "meander": dict(
        variables=[var("x", "cell", "normal", (1, 25))],
        layers=[
            region_layer(),
            layer("given", "已给数字", "number", role="input", var="x", min=1),
            answer_number("x", "解"),
        ],
        rows=6, cols=6, uses_regions=True,
    ),
    "nanro": dict(
        variables=[
            var("x", "cell", "normal", (0, 12), "0 = 不填数"),
            var("f", "cell", "normal", (0, 1), "1 = 该格填了数"),
        ],
        layers=[
            region_layer(),
            layer("given", "已给数字", "number", role="input", var="x", min=0),
            answer_number("x", "填数"),
        ],
        rows=7, cols=7, uses_regions=True,
    ),
    # ----------------------------------------------------------------- 分区
    "fillomino": dict(
        variables=[var("c", "cell", "cc", None, "区域划分"), NUM],
        layers=[clue_number("n", "区域面积"), partition_layer("c")],
        rows=8, cols=8,
    ),
    "shikaku": dict(
        variables=[var("c", "cell", "cc", None, "长方形划分"), NUM],
        layers=[clue_number("n", "长方形面积"), partition_layer("c")],
        rows=8, cols=8,
    ),
    "araf": dict(
        variables=[var("c", "cell", "cc", None, "区域划分"), NUM],
        layers=[clue_number("n", "圆圈数字"), partition_layer("c")],
        rows=7, cols=7,
    ),
    # ----------------------------------------------------------------- 回路
    "slither": dict(
        variables=[var("e", "edge", "normal", (0, 1), "1 = 回路经过该格线"), NUM],
        layers=[
            clue_number("n", "格内线段数", max=4),
            edgeline_layer("e", "回路"),
        ],
        rows=8, cols=8,
    ),
    "masyu": dict(
        variables=[var("e", "edge", "normal", (0, 1), "1 = 回路连接两格"),
                   cell_const("o", "1 = 白圈, 2 = 黑圈")],
        layers=[clue_circle("o", "珍珠"), link_layer("e", "回路")],
        rows=9, cols=9,
    ),
    "simpleloop": dict(
        variables=[var("e", "edge", "normal", (0, 1)), cell_const("w", "1 = 黑格")],
        layers=[
            layer("wall", "黑格", "shade", role="input", var="w", palette={"1": BLACK}),
            link_layer("e", "回路"),
        ],
        rows=8, cols=8,
    ),
    "yajilin": dict(
        variables=[
            var("e", "edge", "normal", (0, 1)),
            var("x", "cell", "normal", (0, 1), "1 = 涂黑"),
            cell_const("d", "箭头方向 0-3"),
            cell_const("n", "该方向黑格数"),
        ],
        layers=[
            clue_arrow("d", "箭头"),
            clue_number("n", "黑格数"),
            shade(),
            link_layer("e", "回路"),
        ],
        rows=9, cols=9,
        notes="提示格既要写方向 d（0=上 1=下 2=左 3=右）也要写数字 n。",
    ),
    "country": dict(
        variables=[var("e", "edge", "normal", (0, 1)), NUM],
        layers=[region_layer(), clue_number("n", "区域内经过格数"), link_layer("e", "回路")],
        rows=8, cols=8, uses_regions=True,
    ),
    "detour": dict(
        variables=[var("e", "edge", "normal", (0, 1)), NUM],
        layers=[region_layer(), clue_number("n", "区域内转弯数"), link_layer("e", "回路")],
        rows=8, cols=8, uses_regions=True,
    ),
    "doubleback": dict(
        variables=[var("e", "edge", "normal", (0, 1))],
        layers=[region_layer(), link_layer("e", "回路")],
        rows=8, cols=8, uses_regions=True,
    ),
}


def main() -> int:
    for key, config in TABLE.items():
        path = write_spec(key, **config)
        print(f"wrote {path.name}")
    print(f"{len(TABLE)} spec(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
