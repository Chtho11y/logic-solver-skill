"""Author a batch of fully-encoded rules that only use existing DSL builtins.

Metadata (en/zh/rule/category) always comes from rules.txt via gen.add.
Run:

    python gen_easy.py
"""
from gen import (
    CAT, ENTRIES, IMPL, SAMP, REGION_LAYER, SHADE_LAYER, add, arrow_layer,
    block_regions, circle_layer, const, num_layer, sample, shade_var,
)

KEYS = []


def easy(key, *args, **kwargs):
    add(key, *args, **kwargs)
    KEYS.append(key)


def fill_var(lo, hi, doc="", name="x"):
    return {"name": name, "kind": "cell", "type": "normal", "domain": [lo, hi],
            "doc": doc}


def cc_var(doc="区域划分", name="c"):
    return {"name": name, "kind": "cell", "type": "cc", "doc": doc}


def edge_var(doc="1 = 回路", name="e"):
    return {"name": name, "kind": "edge", "type": "normal", "domain": [0, 1],
            "doc": doc}


def edge_const(name, doc):
    return {"name": name, "kind": "edge", "type": "constant", "doc": doc}


def given_num(var="x", label="已给数字", mn=0, mx=9):
    return {"id": "given", "label": label, "element": "number", "target": "cell",
            "role": "input", "var": var, "options": {"min": mn, "max": mx}}


def answer_num(var="x", label="解"):
    return {"id": "answer", "label": label, "element": "number", "target": "cell",
            "role": "output", "var": var, "palette": {"*": "#1565c0"}}


def loop_layer(var="e"):
    return {"id": "loop", "label": "回路", "element": "link", "target": "edge",
            "role": "output", "var": var}


def partition_layer(var="c"):
    return {"id": "partition", "label": "分区结果", "element": "region",
            "target": "cell", "role": "output", "var": var}


def outside_layer(sides, mode="int", label="盘外提示"):
    return {"id": "outside", "label": label, "element": "outside",
            "target": "outside", "role": "input", "param": "outside",
            "options": {"sides": sides, "mode": mode}}


def dot_layer(var="d", label="黑白点"):
    return {"id": "dots", "label": label, "element": "dot", "target": "edge",
            "role": "input", "var": var,
            "palette": {"1": "#ffffff", "2": "#232733"}}


def cross_layer(var="m", label="叉号"):
    return {"id": "cross", "label": label, "element": "cross", "target": "cell",
            "role": "input", "var": var}


def star_layer(var="x"):
    return {"id": "star", "label": "星", "element": "star", "target": "cell",
            "role": "output", "var": var}


def grid_clues(rows):
    """rows: list of list/str; '.' skips, ints are values."""
    out = {}
    for r, line in enumerate(rows):
        cells = line.split() if isinstance(line, str) and " " in line else list(line)
        for c, tok in enumerate(cells):
            if tok in {".", "·", "_", " "}:
                continue
            out[f"{r},{c}"] = int(tok)
    return out


def regions_from(rows):
    out = {}
    for r, line in enumerate(rows):
        cells = line.split() if isinstance(line, str) and " " in line else list(line)
        for c, tok in enumerate(cells):
            out[f"{r},{c}"] = int(tok)
    return out


# ---------------------------------------------------------------------------
# 涂黑 II
# ---------------------------------------------------------------------------

easy("binairo",
     '''
# 无三连黑/白；每行每列恰一半涂黑；行互异、列互异；白圈留白、黑圈涂黑。
import "shading"

no_run(x, 1, 3)
no_run(x, 0, 3)
for r in rows:
    num_eq(x[r], 1) == cols.size / 2
for c in cols:
    num_eq(x[c], 1) == rows.size / 2
distinct_rows(x)
distinct_cols(x)

for p in clue_cells(o):
    if at(o, p) == 1:
        at(x, p) == 0
    else:
        at(x, p) == 1
''',
     [shade_var(), const("o", "1 = 白圈必须留白, 2 = 黑圈必须涂黑")],
     [circle_layer("o", "黑白圈"), SHADE_LAYER],
     rows=8, cols=8,
     notes="盘面边长须为偶数。",
     sample=sample("binairo", 4, 4, clues={"o": {"0,0": 1, "0,2": 2, "3,1": 1}}))


# ---------------------------------------------------------------------------
# 放置
# ---------------------------------------------------------------------------

easy("gaps",
     '''
# 每行每列两颗星，星不能接触（含对角）；盘外数字 = 两星之间的空格数。
import "outside"

for r in rows:
    num_eq(x[r], 1) == 2
for c in cols:
    num_eq(x[c], 1) == 2
no_touch(x, 1)
outside_gap_between(x, 1)
''',
     [fill_var(0, 1, "1 = 星")],
     [outside_layer(["left", "top"], label="两星间距"), star_layer()],
     rows=8, cols=8,
     notes="left[r] / top[c] 为该行/列两星之间的空格数；负数或缺省表示无提示。",
     params={"defaults": {"left": [], "top": []}},
     sample=sample("gaps", 8, 8, params={
         "left": [1, 1, 1, 1, 1, 1, 1, 1],
         "top": [1, 1, 1, 1, 1, 1, 1, 1],
     }))

easy("magnets",
     '''
# 每个 1x2 区域空着，或放一正一负；相邻同号禁止；盘外为 +/- 个数。
import "outside"
import "regions"

for reg in regions:
    let plus = num_eq(x[reg], 1)
    let minus = num_eq(x[reg], 2)
    (plus == 0 and minus == 0) or (plus == 1 and minus == 1)

for p in cells():
    for q in adj4(p):
        not (at(x, p) != 0 and at(x, p) == at(x, q))

row_count(x, 1, "left")
row_count(x, 2, "right")
col_count(x, 1, "top")
col_count(x, 2, "bottom")
''',
     [fill_var(0, 2, "0 = 空, 1 = +, 2 = -")],
     [REGION_LAYER, outside_layer(["top", "left", "right", "bottom"], label="+/- 个数"),
      {"id": "poles", "label": "磁极", "element": "shade", "target": "cell",
       "role": "output", "var": "x",
       "palette": {"1": "#c62828", "2": "#1565c0"}}],
     rows=6, cols=6, uses_regions=True,
     notes="1 = 加号, 2 = 减号。left/top 为加号个数，right/bottom 为减号个数。区域须为给定的 1×2。",
     params={"defaults": {"top": [], "left": [], "right": [], "bottom": []}},
     sample=sample("magnets", 2, 2,
                   regions=regions_from(["00", "11"])))


# ---------------------------------------------------------------------------
# 填写
# ---------------------------------------------------------------------------

easy("simplegako",
     '''
# 每个数字等于它在所在行和列中出现的次数（自身只计一次）。
import "core"

for p in cells():
    let v = at(x, p)
    let cnt = 0
    for q in row(row_of(p)):
        let cnt = cnt + b2i(at(x, q) == v)
    for q in col(col_of(p)):
        if row_of(q) != row_of(p):
            let cnt = cnt + b2i(at(x, q) == v)
    v == cnt
''',
     [fill_var(1, 16, "出现次数")],
     [given_num(mn=1, mx=16), answer_num()],
     rows=6, cols=6,
     sample=sample("simplegako", 3, 3, clues={"x": {"0,0": 1, "1,1": 3}}))

easy("bosanowa",
     '''
# 每个正整数等于自身与正交邻格之差的绝对值之和（缺邻视为 0）。
import "core"

for p in cells():
    let s = 0
    for q in adj4(p):
        let s = s + abs(at(x, p) - at(x, q))
    at(x, p) == s
''',
     [fill_var(1, 40, "正整数")],
     [given_num(mn=1, mx=40), answer_num()],
     rows=6, cols=6,
     sample=sample("bosanowa", 3, 3, clues={"x": {"0,0": 1, "1,1": 2}}))

easy("fuzuli",
     '''
# 每行每列 1..k 各一次，其余留空；无 2x2 全填；叉号格必须留空。
import "fill"

let k = param("k")
subset_latin(x, k)
for w in slide(2, 2):
    let filled = 0
    for p in w:
        let filled = filled + b2i(at(x, p) != 0)
    filled < 4
for p in clue_cells(m):
    at(x, p) == 0
''',
     [fill_var(0, 9, "0 = 空"), const("m", "1 = 此格不能填数")],
     [cross_layer(), given_num(mn=1, mx=9), answer_num()],
     rows=6, cols=6,
     notes="params.k 为字母/数字种类数，默认边长-2。",
     params={"defaults": {"k": 4}},
     sample=sample("fuzuli", 4, 4, params={"k": 2},
                   clues={"x": {"0,0": 1, "0,1": 2}, "m": {"0,2": 1}}))

easy("doppelblock",
     '''
# 每行每列两个黑格（0）加上 1..N-2 各一次；盘外数字 = 两黑格之间的数字和。
import "fill"
import "outside"

subset_latin(x, cols.size - 2)
outside_between_sum(x, 0)
''',
     [fill_var(0, 9, "0 = 黑格")],
     [outside_layer(["left", "top"], label="两黑格之间的和"),
      answer_num()],
     rows=6, cols=6,
     notes="0 表示黑格。left[r] / top[c] 为该行/列两黑格之间的数字之和。",
     params={"defaults": {"left": [], "top": []}},
     sample=sample("doppelblock", 4, 4, params={"left": [3, 0, 1, 2], "top": [3, 0, 1, 2]}))

easy("easyasabc",
     '''
# 每行每列字母 1..k 各一次，其余留空；盘外字母是该方向看到的第一个字母。
import "fill"
import "outside"

let k = param("k")
subset_latin(x, k)
outside_first_letter(x)
''',
     [fill_var(0, 9, "0 = 空, 1 = A, 2 = B, …")],
     [outside_layer(["top", "left", "right", "bottom"], label="第一字母"),
      given_num(mn=1, mx=9), answer_num()],
     rows=6, cols=6,
     notes="1=A, 2=B, …。params.k 为字母种数。",
     params={"defaults": {"k": 3, "top": [], "left": [], "right": [], "bottom": []}},
     sample=sample("easyasabc", 3, 3, params={"k": 2, "left": [1, 2, 1], "top": [1, 2, 1]}))

easy("skyscrapers",
     '''
# 每行每列 1..k 各一次（k=N 时即拉丁方）；盘外数字 = 该方向可见的摩天楼数。
# 0 表示空地，不遮挡视线。
import "fill"
import "outside"

let k = param("k")
subset_latin(x, k)
outside_visible(x)
''',
     [fill_var(0, 9, "0 = 空, 1..k = 楼高")],
     [outside_layer(["top", "left", "right", "bottom"], label="可见楼数"),
      given_num(mn=1, mx=9), answer_num()],
     rows=6, cols=6,
     notes="params.k 为最高楼层，默认等于边长（全填拉丁方）。空地不遮挡。",
     params={"defaults": {"k": 6, "top": [], "left": [], "right": [], "bottom": []}},
     sample=sample("skyscrapers", 3, 3,
                   params={"k": 3, "left": [2, 1, 2], "top": [2, 3, 1]}))

easy("kropki",
     '''
# 拉丁方 1..N。白点差 1，黑点比 1:2；无点则既非连续也非倍半。1 与 2 两种点都行。
import "fill"

latin_1_to_n(x)

for e in clue_cells(d):
    let cs = cell_of(e)
    if cs.size == 2:
        let a = at(x, cs[0])
        let b = at(x, cs[1])
        if at(d, e) == 1:
            kropki_white(a, b)
        else:
            kropki_black(a, b)
    else:
        false

for p in cells():
    let q = shift(p, 0, 1)
    if q.size == 1:
        let e = edge("V", row_of(p), col_of(p) + 1)
        if not has_value(d, e):
            not kropki_white(at(x, p), at(x, q)) and not kropki_black(at(x, p), at(x, q))
    let q2 = shift(p, 1, 0)
    if q2.size == 1:
        let e = edge("H", row_of(p) + 1, col_of(p))
        if not has_value(d, e):
            not kropki_white(at(x, p), at(x, q2)) and not kropki_black(at(x, p), at(x, q2))
''',
     [fill_var(1, 9, "1..N"), edge_const("d", "1 = 白点, 2 = 黑点")],
     [dot_layer(), given_num(mn=1, mx=9), answer_num()],
     rows=6, cols=6,
     notes="点画在相邻两格之间的格线上。1 与 2 相邻时必须有点，黑白均可。",
     sample=sample("kropki", 2, 2, clues={
         "x": {"0,0": 1},
         "d": {"V,0,1": 1, "V,1,1": 1, "H,1,0": 1, "H,1,1": 1},
     }))

easy("kropki-pairs",
     '''
# 拉丁方 1..N。只对给出的黑白点施加差 1 / 比 1:2；未给出的邻格不限制。
import "fill"

latin_1_to_n(x)

for e in clue_cells(d):
    let cs = cell_of(e)
    if cs.size == 2:
        let a = at(x, cs[0])
        let b = at(x, cs[1])
        if at(d, e) == 1:
            kropki_white(a, b)
        else:
            kropki_black(a, b)
    else:
        false
''',
     [fill_var(1, 9, "1..N"), edge_const("d", "1 = 白点, 2 = 黑点")],
     [dot_layer(), given_num(mn=1, mx=9), answer_num()],
     rows=6, cols=6,
     sample=sample("kropki-pairs", 3, 3, clues={
         "x": {"0,0": 1},
         "d": {"V,0,1": 1, "H,1,0": 1},
     }))

easy("cojun",
     '''
# 每个区域 1..N；正交相邻不同；同一区域里上方必须比下方大。
import "fill"

region_1_to_n(x)
adjacent_differ(x)
for p in cells():
    let q = shift(p, 1, 0)
    if q.size == 1:
        if same_region(p, q):
            at(x, p) > at(x, q)
''',
     [fill_var(1, 16, "1..N")],
     [REGION_LAYER, given_num(mn=1, mx=16), answer_num()],
     rows=8, cols=8, uses_regions=True,
     sample=sample("cojun", 2, 2, regions=block_regions(2, 2, 2, 2),
                   clues={"x": {"0,0": 4}}))

easy("hanare",
     '''
# 每区恰好填一个等于区域面积的数；同行/列且中间无其他数字时，中间空格数 = 两数之差。
import "core"

for reg in regions:
    let nz = 0
    for p in reg:
        let nz = nz + b2i(at(x, p) != 0)
        at(x, p) == 0 or at(x, p) == reg.size
    nz == 1

for p in cells():
    for q in cells():
        if row_of(p) == row_of(q):
            if col_of(p) < col_of(q):
                let blocked = 0
                for t in row(row_of(p)):
                    if col_of(p) < col_of(t):
                        if col_of(t) < col_of(q):
                            let blocked = blocked + b2i(at(x, t) != 0)
                (at(x, p) != 0 and at(x, q) != 0 and blocked == 0) => (col_of(q) - col_of(p) - 1 == abs(at(x, p) - at(x, q)))
        if col_of(p) == col_of(q):
            if row_of(p) < row_of(q):
                let blocked = 0
                for t in col(col_of(p)):
                    if row_of(p) < row_of(t):
                        if row_of(t) < row_of(q):
                            let blocked = blocked + b2i(at(x, t) != 0)
                (at(x, p) != 0 and at(x, q) != 0 and blocked == 0) => (row_of(q) - row_of(p) - 1 == abs(at(x, p) - at(x, q)))
''',
     [fill_var(0, 20, "0 = 空, 否则 = 区域面积")],
     [REGION_LAYER, given_num(mn=1, mx=20), answer_num()],
     rows=8, cols=8, uses_regions=True,
     sample=sample("hanare", 2, 2, regions=regions_from(["01", "01"])))

easy("makaro",
     '''
# 非箭头格：区域内 1..N（N = 非箭头格数）；相邻数字不同。
# 箭头指向其正交数字邻格中唯一最大的那个。
import "core"

for reg in regions:
    let nwhite = 0
    for p in reg:
        if not has_value(d, p):
            let nwhite = nwhite + 1
    for p in reg:
        if has_value(d, p):
            at(x, p) == 0
        else:
            at(x, p) >= 1
            at(x, p) <= nwhite
    for p in reg:
        for q in reg:
            if before(p, q):
                if not has_value(d, p):
                    if not has_value(d, q):
                        at(x, p) != at(x, q)

for p in cells():
    for q in adj4(p):
        (at(x, p) != 0 and at(x, q) != 0) => at(x, p) != at(x, q)

for p in clue_cells(d):
    let tgt = step(p, at(d, p))
    if tgt.size == 0:
        false
    else:
        at(x, tgt) != 0
        for q in adj4(p):
            if row_of(q) != row_of(tgt) or col_of(q) != col_of(tgt):
                at(x, q) != 0 => at(x, q) < at(x, tgt)
''',
     [fill_var(0, 16, "0 = 黑格/箭头格"), const("d", "箭头 0-3")],
     [REGION_LAYER, arrow_layer("d", "极大箭头"), given_num(mn=1, mx=16), answer_num()],
     rows=8, cols=8, uses_regions=True,
     notes="箭头格不填数。0=上 1=下 2=左 3=右。",
     sample=sample("makaro", 2, 2, regions=block_regions(2, 2, 2, 2),
                   clues={"x": {"0,0": 4}}))


# ---------------------------------------------------------------------------
# 分区
# ---------------------------------------------------------------------------

easy("fourcells",
     '''
# 分成四格骨牌；数字 = 此格四条边中属于区域边界（含盘边）的条数。
import "regions"
import "loops"

all_regions_size(c, 4)
for p in clue_cells(n):
    cell_edge_count(c.border, p) == at(n, p)
''',
     [cc_var(), const("n", "边界边数 0-4")],
     [num_layer("n", "边界边数", options={"min": 0, "max": 4}), partition_layer()],
     rows=8, cols=8,
     notes="盘面格数须是 4 的倍数。",
     sample=sample("fourcells", 4, 4, clues={"n": {"0,0": 2}}))

easy("fivecells",
     '''
# 分成五格骨牌；数字 = 此格四条边中属于区域边界（含盘边）的条数。
import "regions"
import "loops"

all_regions_size(c, 5)
for p in clue_cells(n):
    cell_edge_count(c.border, p) == at(n, p)
''',
     [cc_var(), const("n", "边界边数 0-4")],
     [num_layer("n", "边界边数", options={"min": 0, "max": 4}), partition_layer()],
     rows=10, cols=10,
     notes="盘面格数须是 5 的倍数。",
     sample=sample("fivecells", 5, 5, clues={"n": {"0,0": 2}}))

easy("meadows",
     '''
# 分成正方形；每个区域恰好一个黑圈。
import "regions"

regions_are_squares(c)
one_clue_per_region(c, o)
for p in clue_cells(o):
    region_width(c, p) == region_height(c, p)
''',
     [cc_var(), const("o", "2 = 黑圈")],
     [circle_layer("o", "黑圈"), partition_layer()],
     rows=8, cols=8,
     sample=sample("meadows", 2, 2, clues={"o": {"0,0": 2}}))

easy("squarejam",
     '''
# 分成正方形；顶点处不能四区相会；数字 = 所在正方形边长。
import "regions"

regions_are_squares(c)
no_four_regions_at_vertex(c)
for p in clue_cells(n):
    region_width(c, p) == at(n, p)
''',
     [cc_var(), const("n", "边长")],
     [num_layer("n", "边长"), partition_layer()],
     rows=8, cols=8,
     sample=sample("squarejam", 2, 2, clues={"n": {"0,0": 2}}))

easy("tatamibari",
     '''
# 分成矩形，每区一个符号；顶点处不能四区相会。
# 1 = 加号（正方形），2 = 横线（宽>高），3 = 竖线（高>宽）。
import "regions"

regions_are_rectangles(c)
one_clue_per_region(c, s)
no_four_regions_at_vertex(c)
for p in clue_cells(s):
    if at(s, p) == 1:
        region_width(c, p) == region_height(c, p)
    elif at(s, p) == 2:
        region_width(c, p) > region_height(c, p)
    else:
        region_height(c, p) > region_width(c, p)
''',
     [cc_var(), const("s", "1 = +, 2 = —, 3 = |")],
     [num_layer("s", "符号 1=+ 2=横 3=竖", options={"min": 1, "max": 3}),
      partition_layer()],
     rows=8, cols=8,
     notes="符号：1 加号正方形，2 横线宽大于高，3 竖线高大于宽。",
     sample=sample("tatamibari", 2, 2, clues={"s": {"0,0": 1}}))

easy("domino-search",
     '''
# 分成 1x2；盘面数字给定，每种无序数对至多出现在一个骨牌上。
import "regions"

all_regions_size(c, 2)
for p in cells():
    for q in adj4(p):
        if before(p, q):
            for p2 in cells():
                for q2 in adj4(p2):
                    if before(p2, q2):
                        if before(p, p2) or (row_of(p) == row_of(p2) and col_of(p) == col_of(p2) and before(q, q2)):
                            if same_pair(p, q, p2, q2):
                                not (at(c, p) == at(c, q) and at(c, p2) == at(c, q2))

def same_pair(p, q, p2, q2):
    if at(n, p) == at(n, p2):
        if at(n, q) == at(n, q2):
            return true
    if at(n, p) == at(n, q2):
        if at(n, q) == at(n, p2):
            return true
    return false
''',
     [cc_var(), const("n", "盘面数字")],
     [num_layer("n", "盘面数字"), partition_layer()],
     rows=6, cols=6,
     notes="数字应填满盘面。相同无序数对不能出现在两个骨牌上。",
     sample=sample("domino-search", 2, 2, clues={"n": {"0,0": 1, "0,1": 2, "1,0": 1, "1,1": 3}}))

easy("lapaz",
     '''
# 黑格孤立；其余划分成 1x2（骨牌可以相邻）。数字格不涂黑。
# 横骨牌上的数字 = 该行黑格数；竖骨牌上的数字 = 该列黑格数。
import "regions"
import "shading"

no_adjacent(x, 1)
clue_cells_white(x, n)

for p in cells():
    at(x, p) == 1 => at(c.size, p) == 1
    at(x, p) == 0 => at(c.size, p) == 2

for p in clue_cells(n):
    let horiz = false
    let left = shift(p, 0, -1)
    let right = shift(p, 0, 1)
    if left.size == 1:
        let horiz = horiz or (at(c, p) == at(c, left))
    if right.size == 1:
        let horiz = horiz or (at(c, p) == at(c, right))
    at(n, p) == ite(horiz, num_eq(x[row(row_of(p))], 1), num_eq(x[col(col_of(p))], 1))
''',
     [shade_var(), cc_var(), const("n", "行或列黑格数")],
     [num_layer("n", "行/列黑格数"), SHADE_LAYER, partition_layer()],
     rows=8, cols=8,
     notes="黑格各自成区；留白格两两成骨牌（骨牌之间可以相邻）。",
     sample=sample("lapaz", 2, 2, clues={"n": {"0,0": 0}}))

easy("symmarea",
     '''
# Fillomino：相邻区域面积不同，数字 = 面积；每个区域 180° 旋转对称。
import "regions"

neighbour_sizes_differ(c)
region_size_clue(c, n)
region_180_symmetric(c)
''',
     [cc_var(), const("n", "区域面积")],
     [num_layer("n", "区域面积"), partition_layer()],
     rows=8, cols=8,
     sample=sample("symmarea", 3, 3, clues={"n": {"1,1": 9}}))

easy("wafusuma",
     '''
# Fillomino 邻区面积不同；格线上数字 = 两侧区域面积之和（两侧必须不同区）。
import "regions"

neighbour_sizes_differ(c)
for e in clue_cells(k):
    let cs = cell_of(e)
    if cs.size == 2:
        at(c, cs[0]) != at(c, cs[1])
        at(c.size, cs[0]) + at(c.size, cs[1]) == at(k, e)
    else:
        false
''',
     [cc_var(), edge_const("k", "两侧面积和")],
     [{"id": "clue_k", "label": "邻区面积和", "element": "number", "target": "edge",
       "role": "input", "var": "k", "options": {"min": 1}},
      partition_layer()],
     rows=8, cols=8,
     notes="数字写在两格之间的格线上。",
     sample=sample("wafusuma", 2, 2, clues={"k": {"V,0,1": 4}}))


# ---------------------------------------------------------------------------
# 回路 I / II
# ---------------------------------------------------------------------------

easy("midloop",
     '''
# 回路笔直经过每个黑点，且黑点是该直线段的中点。
import "loops"

cloop(e)
for p in clue_cells(o):
    on_loop(e, p)
    goes_straight(e, p)
    used_arm_len(e, p, LEFT) == used_arm_len(e, p, RIGHT)
    used_arm_len(e, p, UP) == used_arm_len(e, p, DOWN)
''',
     [edge_var(), const("o", "黑点")],
     [circle_layer("o", "中点"), loop_layer()],
     rows=8, cols=8,
     sample=sample("midloop", 2, 3, clues={"o": {"0,1": 2, "1,1": 2}}))

easy("geradeweg",
     '''
# 回路经过所有圆圈。圈中数字 = 穿过该圈的直线段长度。
import "loops"

cloop(e)
for p in clue_cells(o):
    on_loop(e, p)
for p in clue_cells(n):
    on_loop(e, p)
    goes_straight(e, p)
    straight_len_through(e, p) == at(n, p)
''',
     [edge_var(), const("o", "圆圈"), const("n", "直线段长度")],
     [circle_layer("o", "圆圈"), num_layer("n", "段长"), loop_layer()],
     rows=8, cols=8,
     notes="无数字的圆圈仍须在回路上。",
     sample=sample("geradeweg", 2, 3, clues={"o": {"0,1": 1}, "n": {"0,1": 3}}))

easy("balance",
     '''
# 回路经过所有圆圈。白圈两臂等长，黑圈两臂不等；数字 = 两臂长度之和。
import "loops"

cloop(e)
for p in clue_cells(o):
    on_loop(e, p)
    if at(o, p) == 1:
        two_arms_equal(e, p)
    else:
        not two_arms_equal(e, p)
for p in clue_cells(n):
    on_loop(e, p)
    two_arm_sum(e, p) == at(n, p)
''',
     [edge_var(), const("o", "1 = 白圈等长, 2 = 黑圈不等"), const("n", "两臂之和")],
     [circle_layer("o", "平衡圈"), num_layer("n", "两臂之和"), loop_layer()],
     rows=8, cols=8,
     sample=sample("balance", 2, 3, clues={"o": {"0,1": 1}, "n": {"0,1": 2}}))

easy("yajilin-regions",
     '''
# 回路经过所有未涂黑格；黑格不相邻；数字 = 该区域黑格数。
import "loops"
import "shading"

loop_visits_all_but(e, x)
no_adjacent(x, 1)
region_black_count(x, n)
''',
     [edge_var(), shade_var(), const("n", "区域黑格数")],
     [REGION_LAYER, num_layer("n", "区域黑格数"), SHADE_LAYER, loop_layer()],
     rows=8, cols=8, uses_regions=True,
     sample=sample("yajilin-regions", 4, 4,
                   regions=block_regions(4, 4, 4, 4),
                   clues={"n": {"0,0": 0}}))

easy("koburin",
     '''
# 仙人指路 + 数字格不在回路上、不涂黑，数字 = 正交邻格黑格数。
import "loops"
import "core"

cloop(e)
no_adjacent(x, 1)
for p in cells():
    if has_value(n, p):
        at(x, p) == 0
        off_loop(e, p)
        n_adj4(x, p, 1) == at(n, p)
    else:
        on_loop(e, p) == (at(x, p) == 0)
''',
     [edge_var(), shade_var(), const("n", "邻格黑格数")],
     [num_layer("n", "邻格黑格数"), SHADE_LAYER, loop_layer()],
     rows=8, cols=8,
     notes="数字格既不涂黑也不在回路上。",
     sample=sample("koburin", 3, 3, clues={"n": {"1,1": 0}}))

easy("nuriloop",
     '''
# 回路；不在回路上的格子构成若干连通岛，每岛恰好一个数字，数字 = 岛的格数。
import "loops"
import "core"

cloop(e)
for p in cells():
    on_loop(e, p) == (at(x, p) == 0)
for p in clue_cells(n):
    at(x, p) == 1
    at(cc_size(x), p) == at(n, p)
cc_count(x, 1) == clue_cells(n).size
''',
     [edge_var(), shade_var(), const("n", "离岛格数")],
     [num_layer("n", "离岛格数"), SHADE_LAYER, loop_layer()],
     rows=8, cols=8,
     notes="x = 1 表示不在回路上。无数字时回路经过全部格子。",
     sample=sample("nuriloop", 4, 4))


# ---------------------------------------------------------------------------
# 路径 II
# ---------------------------------------------------------------------------

easy("hidato",
     '''
# 填入 1..N 各一次（N = 总格数）；连续数字必须八邻域相邻。
import "core"

let n = rows.size * cols.size
for p in cells():
    at(x, p) >= 1
    at(x, p) <= n
for p in cells():
    for q in cells():
        if before(p, q):
            at(x, p) != at(x, q)
for p in cells():
    let ok = b2i(at(x, p) == n)
    for q in adj8(p):
        let ok = ok + b2i(at(x, q) == at(x, p) + 1)
    ok >= 1
''',
     [fill_var(1, 81, "1..N")],
     [given_num(mn=1, mx=81), answer_num()],
     rows=8, cols=8,
     sample=sample("hidato", 3, 3, clues={"x": {"0,0": 1, "2,2": 9}}))


def main():
    import json
    from gen import ENTRIES as ALL
    for key in KEYS:
        spec, dsl, sm, status = ALL[key]
        (IMPL / f"{key}.json").write_text(
            json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (IMPL / f"{key}.dsl").write_text(dsl, encoding="utf-8")
        if sm is None:
            sm = sample(key, regions=block_regions(6, 6) if spec["usesRegions"] else None)
        (SAMP / f"{key}.json").write_text(
            json.dumps(sm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(KEYS)} easy rules: {' '.join(KEYS)}")


if __name__ == "__main__":
    main()
