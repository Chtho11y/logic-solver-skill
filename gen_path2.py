"""Write spec JSON + samples for remaining 路径I / 路径II rules."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tools.scaffold import (  # noqa: E402
    LOOP_VAR,
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

E_PATH = var("e", "edge", "normal", (0, 1), "1 = 路径")
X_ID = var("x", "cell", "normal", (0, 36), "路径编号 / 访问序；0=未经过")
GRAY = "#bdbdbd"
ICE = "#90caf9"
GREEN = "#66bb6a"
WATER = "#42a5f5"


def _write():
    write_spec(
        "wblink",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (0, 20), "配对编号；0=未经过"),
            var("o", "cell", "constant", doc="1=白圈 2=黑圈"),
        ],
        layers=[clue_circle("o", "圆圈"), layer("answer", "配对编号", "number", role="output", var="x"), link_layer("e", "路径")],
        rows=8, cols=8,
        notes="黑白两两配对，路径可转弯、不交叉。",
    )
    write_sample("wblink", sample(
        "wblink", 1, 2, title="1x2 一对接",
        clues={"o": from_grid("1 2")},
    ))

    write_spec(
        "walllogic",
        variables=[
            E_PATH,
            var("n", "cell", "constant", doc="箭头占用总格数"),
        ],
        layers=[clue_number("n", "数字"), link_layer("e", "箭头")],
        rows=8, cols=8,
        notes="空格均被某数字的直臂覆盖；数字=四向臂长之和。",
    )
    write_sample("walllogic", sample(
        "walllogic", 1, 3, title="1x3 四风",
        clues={"n": from_grid("2 . .")},
    ))

    write_spec(
        "hashi",
        variables=[
            var("e", "edge", "normal", (0, 1), "1 = 至少一座桥"),
            var("t", "edge", "normal", (0, 1), "1 = 双桥（额外一座）"),
            var("n", "cell", "constant", doc="岛上数字"),
        ],
        layers=[
            clue_circle("n", "岛屿"),
            clue_number("n", "数字"),
            link_layer("e", "桥梁"),
        ],
        rows=8, cols=8,
        notes="t 为双桥辅助边，不单独绘制。岛与桥格不能斜向误连，连通走占用边。",
    )
    write_sample("hashi", sample(
        "hashi", 1, 3, title="1x3 单桥",
        clues={"n": from_grid("1 . 1")},
    ))

    write_spec(
        "coffeemilk",
        variables=[
            E_PATH,
            var("u", "cell", "normal", (0, 36), "所属灰圈编号"),
            var("o", "cell", "constant", doc="1=白 2=黑 3=灰"),
        ],
        layers=[clue_circle("o", "圆圈"), link_layer("e", "线段")],
        rows=8, cols=8,
        notes="u 为辅助：每组用其灰圈下标作编号。",
    )
    write_sample("coffeemilk", sample(
        "coffeemilk", 1, 3, title="1x3 咖啡牛奶",
        clues={"o": from_grid("2 3 1")},
    ))

    write_spec(
        "kaero",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (0, 36), "字母实例编号"),
            var("f", "cell", "normal", (0, 9), "落点字母；0=空"),
            var("n", "cell", "constant", doc="字母种类"),
        ],
        layers=[
            region_layer(),
            clue_number("n", "字母"),
            layer("dest", "落点", "number", role="output", var="f"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8, uses_regions=True,
        notes="每个字母实例一条可转弯路径；落点后每区一种字母且同字母同区。",
    )
    write_sample("kaero", sample(
        "kaero", 2, 2, title="2x2 归路",
        clues={"n": from_grid("""
            1 2
            . .
        """)},
        regions=block_regions(2, 2, 2, 1),
    ))

    write_spec(
        "bonsan",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (0, 36), "圆圈编号"),
            var("f", "cell", "normal", (0, 1), "1 = 落点有圆圈"),
            var("o", "cell", "constant", doc="1 = 圆圈"),
            var("n", "cell", "constant", doc="移动距离"),
        ],
        layers=[
            clue_circle("o", "圆圈"),
            clue_number("n", "距离"),
            shade("f", "落点", role="output"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8,
        notes="直线滑动；落点盘面 180° 中心对称。",
    )
    write_sample("bonsan", sample(
        "bonsan", 2, 2, title="2x2 已对称",
        clues={"o": from_grid("""
            1 .
            . 1
        """)},
    ))

    write_spec(
        "sato",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (0, 36), "圆圈编号"),
            var("f", "cell", "normal", (0, 1), "1 = 落点有圆圈"),
            var("o", "cell", "constant", doc="1 = 圆圈"),
            var("n", "cell", "constant", doc="移动距离"),
        ],
        layers=[
            region_layer(),
            clue_circle("o", "圆圈"),
            clue_number("n", "距离"),
            shade("f", "落点", role="output"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8, uses_regions=True,
        notes="直线滑动；每区域恰好一个落点。",
    )
    write_sample("sato", sample(
        "sato", 2, 2, title="2x2 回娘家",
        clues={"o": from_grid("""
            1 .
            1 .
        """)},
        regions=block_regions(2, 2, 2, 1),
    ))

    write_spec(
        "forestwalk",
        variables=[
            E_PATH,
            var("u", "cell", "normal", (0, 36), "白段编号"),
            var("z", "cell", "normal", (0, 36), "白段根距离"),
            var("g", "cell", "constant", doc="1 = 绿格"),
            var("n", "cell", "constant", doc="白段格数"),
        ],
        layers=[
            layer("green", "绿格", "shade", role="input", var="g", palette={"1": GREEN}),
            clue_number("n", "白段长度"),
            link_layer("e", "网络"),
        ],
        rows=8, cols=8,
        notes="绿格度数 3，白格 0 或 2；u/z 辅助编码白段。",
    )
    write_sample("forestwalk", sample(
        "forestwalk", 2, 2, title="2x2 白环",
        clues={"n": from_grid("""
            4 .
            . .
        """)},
    ))

    write_spec(
        "yosenabe",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (0, 36), "圆圈编号"),
            var("f", "cell", "normal", (0, 1), "1 = 落点"),
            var("o", "cell", "constant", doc="1 = 圆圈"),
            var("n", "cell", "constant", doc="圆圈数字"),
            var("g", "cell", "constant", doc="1 = 锅"),
            var("k", "cell", "constant", doc="锅内数字和"),
        ],
        layers=[
            region_layer(),
            layer("pot", "灰色锅", "shade", role="input", var="g", palette={"1": GRAY}),
            clue_circle("o", "圆圈"),
            clue_number("n", "圆圈数字"),
            layer("sum", "锅和", "number", role="input", var="k"),
            shade("f", "落点", role="output"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8, uses_regions=True,
        notes="直线滑入灰格；可越过其他锅。k 为锅内圆圈数字之和。",
    )
    write_sample("yosenabe", sample(
        "yosenabe", 2, 2, title="2x2 火锅",
        clues={
            "o": from_grid("""
                1 .
                . .
            """),
            "n": from_grid("""
                3 .
                . .
            """),
            "g": from_grid("""
                . .
                1 1
            """),
            "k": from_grid("""
                . .
                3 .
            """),
        },
        regions={"0,0": 0, "0,1": 0, "1,0": 1, "1,1": 1},
    ))

    write_spec(
        "rectslider",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (0, 36), "黑格编号"),
            var("f", "cell", "normal", (0, 1), "1 = 落点黑格"),
            var("b", "cell", "constant", doc="1 = 起始黑格"),
            var("n", "cell", "constant", doc="移动距离"),
        ],
        layers=[
            layer("start", "起始黑格", "shade", role="input", var="b", palette={"1": "#232733"}),
            clue_number("n", "距离"),
            shade("f", "落点", role="output"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8,
        notes="直线滑动；落点连通组均为面积≥2 的矩形。",
    )
    write_sample("rectslider", sample(
        "rectslider", 1, 2, title="1x2 已是矩形",
        clues={"b": from_grid("1 1"), "n": from_grid("0 0")},
    ))

    write_spec(
        "pmemory",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (0, 36), "沿路径访问序；0=未经过"),
            var("o", "cell", "constant", doc="2 = 黑圈端点"),
            var("g", "cell", "constant", doc="1 = 灰区格"),
        ],
        layers=[
            region_layer(),
            layer("gray", "灰区", "shade", role="input", var="g", palette={"1": GRAY}),
            clue_circle("o", "端点"),
            layer("order", "访问序", "number", role="output", var="x"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8, uses_regions=True,
        notes="蛇形路径；同形同向灰区内部连线一致。",
    )
    write_sample("pmemory", sample(
        "pmemory", 2, 3, title="2x3 记忆",
        clues={
            "o": from_grid("""
                2 . 2
                . . .
            """),
            "g": from_grid("""
                . . .
                . 1 .
            """),
        },
        regions={
            "0,0": 0, "0,1": 0, "0,2": 0,
            "1,0": 0, "1,1": 1, "1,2": 0,
        },
    ))

    write_spec(
        "firefly",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (0, 36), "发出此光束的萤火虫编号"),
            var("o", "cell", "constant", doc="1 = 萤火虫"),
            var("d", "cell", "constant", doc="黑点方向"),
            var("n", "cell", "constant", doc="引出路径转弯次数"),
        ],
        layers=[
            clue_circle("o", "萤火虫"),
            clue_arrow("d", "黑点方向"),
            clue_number("n", "转弯数"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8,
        notes="格心连线：黑点方向迈出第一步，在另一萤火虫非黑点侧结束。",
    )
    write_sample("firefly", sample(
        "firefly", 2, 2, title="2x2 自环",
        clues={
            "o": from_grid("""
                1 .
                . .
            """),
            "d": from_grid("""
                3 .
                . .
            """),
            "n": from_grid("""
                3 .
                . .
            """),
        },
    ))

    write_spec(
        "icebarn",
        variables=[
            E_PATH,
            var("m", "cell", "constant", doc="1=IN 2=OUT"),
            var("d", "cell", "constant", doc="箭头方向"),
            var("g", "cell", "constant", doc="1 = 冰"),
        ],
        layers=[
            region_layer(),
            layer("ice", "冰面", "shade", role="input", var="g", palette={"1": ICE}),
            layer("sg", "IN/OUT", "number", role="input", var="m"),
            clue_arrow("d", "箭头"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8, uses_regions=True,
        notes="冰格可十字自交且不得转弯。箭头约束为沿该轴穿过（方向感在自交时为松弛）。",
    )
    write_sample("icebarn", sample(
        "icebarn", 1, 3, title="1x3 无冰",
        clues={
            "m": from_grid("1 . 2"),
            "d": from_grid("3 . 3"),
        },
        regions={"0,0": 0, "0,1": 0, "0,2": 0},
    ))

    write_spec(
        "herugolf",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (0, 36), "沿球路径的步序"),
            var("u", "cell", "normal", (0, 36), "球编号"),
            var("r", "cell", "normal", (0, 8), "本杆剩余步数"),
            var("s", "cell", "normal", (0, 8), "本杆长度"),
            var("o", "cell", "constant", doc="1 = 球"),
            var("n", "cell", "constant", doc="第一杆长度"),
            var("h", "cell", "constant", doc="1 = H 洞"),
            var("w", "cell", "constant", doc="1 = 水坑"),
        ],
        layers=[
            clue_circle("o", "球"),
            clue_number("n", "第一杆"),
            layer("hole", "洞", "text", role="input", var="h"),
            layer("water", "水坑", "shade", role="input", var="w", palette={"1": WATER}),
            layer("order", "步序", "number", role="output", var="x"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8,
        notes="r/s 为杆数状态。每杆直线；停点不在水上；不可 180° 掉头。",
    )
    write_sample("herugolf", sample(
        "herugolf", 1, 2, title="1x2 一杆进洞",
        clues={"o": from_grid("1 ."), "n": from_grid("1 ."), "h": from_grid(". 1")},
    ))

    write_spec(
        "haisu",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (1, 36), "访问序 1..N"),
            var("m", "cell", "constant", doc="1=S 2=G"),
            var("n", "cell", "constant", doc="第几次进入本区"),
        ],
        layers=[
            region_layer(),
            layer("sg", "S/G", "number", role="input", var="m"),
            clue_number("n", "入区次数"),
            layer("order", "访问序", "number", role="output", var="x"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8, uses_regions=True,
        notes="哈密顿路径 S→G；数字=该格所在停留是本区第几次进入。domain 上限 36。",
    )
    write_sample("haisu", sample(
        "haisu", 2, 2, title="2x2 单区",
        clues={
            "m": from_grid("""
                1 2
                . .
            """),
            "n": from_grid("""
                1 1
                1 1
            """),
        },
        regions=block_regions(2, 2, 2, 2),
    ))

    write_spec(
        "rassi",
        variables=[E_PATH],
        layers=[region_layer(), link_layer("e", "路径")],
        rows=8, cols=8, uses_regions=True,
        notes="每区一条哈密顿路径；所有端点互不接触（含对角）。",
    )
    write_sample("rassi", sample(
        "rassi", 1, 3, title="1x3 单区",
        regions={"0,0": 0, "0,1": 0, "0,2": 0},
    ))

    write_spec(
        "keywest",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (0, 4), "填入的 0~4"),
            var("o", "cell", "constant", doc="1 = 圆圈"),
        ],
        layers=[
            clue_circle("o", "圆圈"),
            layer("num", "填数", "number", role="output", var="x"),
            link_layer("e", "连线"),
        ],
        rows=8, cols=8,
        notes="只在相邻圆圈间连线；>0 的圆圈连通；邻圈数字不同。",
    )
    write_sample("keywest", sample(
        "keywest", 2, 2, title="2x2 群岛",
        clues={"o": from_grid("""
            1 1
            1 1
        """)},
    ))

    write_spec(
        "mintonette",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (0, 20), "配对编号"),
            var("o", "cell", "constant", doc="1 = 圆圈"),
            var("n", "cell", "constant", doc="路径转弯次数"),
        ],
        layers=[
            clue_circle("o", "圆圈"),
            clue_number("n", "转弯数"),
            layer("pair", "配对编号", "number", role="output", var="x"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8,
        notes="覆盖全部格子的两两配对；数字=该路径转弯格数。",
    )
    write_sample("mintonette", sample(
        "mintonette", 2, 2, title="2x2 数弯",
        clues={
            "o": from_grid("""
                1 1
                . .
            """),
            "n": from_grid("""
                2 2
                . .
            """),
        },
    ))

    write_spec(
        "curvedata",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (0, 36), "所属提示编号"),
            var("o", "cell", "constant", doc="1 = 提示格"),
        ],
        layers=[
            clue_circle("o", "提示"),
            layer("fig", "图形编号", "number", role="output", var="x"),
            link_layer("e", "线段"),
        ],
        rows=8, cols=8,
        notes="部分实现：每格都在某图形上，每图恰好一个提示。提示形状的伸缩匹配未编码。",
        unencoded=[],
    )
    write_sample("curvedata", sample(
        "curvedata", 1, 2, title="1x2 单提示",
        clues={"o": from_grid("1 .")},
    ))

    write_spec(
        "icelom",
        variables=[
            E_PATH,
            var("m", "cell", "constant", doc="1=IN 2=OUT"),
            var("n", "cell", "constant", doc="经过顺序"),
            var("g", "cell", "constant", doc="1 = 冰"),
        ],
        layers=[
            layer("ice", "冰面", "shade", role="input", var="g", palette={"1": ICE}),
            layer("sg", "IN/OUT", "number", role="input", var="m"),
            clue_number("n", "顺序"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8,
        notes="部分实现：冰格可自交且不转弯，白格全经过。数字顺序在冰面自交时无法用单次访问序编码。",
        unencoded=["n"],
    )
    write_sample("icelom", sample(
        "icelom", 1, 3, title="1x3 无冰",
        clues={"m": from_grid("1 . 2")},
    ))

    write_spec(
        "anglers",
        variables=[
            E_PATH,
            var("x", "cell", "normal", (0, 20), "路径编号"),
            var("n", "cell", "constant", doc="路径长度"),
            var("o", "cell", "constant", doc="2 = 鱼"),
        ],
        layers=[
            clue_number("n", "长度"),
            clue_circle("o", "鱼"),
            layer("pid", "路径编号", "number", role="output", var="x"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8,
        notes="覆盖全部格子；数字连到唯一一条鱼；数字=路径格数。",
    )
    write_sample("anglers", sample(
        "anglers", 2, 2, title="2x2 渔夫",
        clues={
            "n": from_grid("""
                4 .
                . .
            """),
            "o": from_grid("""
                . 2
                . .
            """),
        },
    ))


if __name__ == "__main__":
    _write()
    print("wrote 路径I/II specs and samples")
