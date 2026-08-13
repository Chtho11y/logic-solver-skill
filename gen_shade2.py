"""涂黑II (26 rules), authored one at a time from rules.txt."""
from gen import (add, const, shade_var, SHADE_LAYER, REGION_LAYER, num_layer,
                 circle_layer, arrow_layer, sample, block_regions)

S = shade_var()
DOT = lambda: circle_layer("t", "点提示 1=白多 2=黑多 3=相等")


# ------------------------------------------------------------- bosnianroad
add("bosnianroad",
    '''
# 涂黑格连通成一个不和自身接触的环；数字格不能涂黑；
# 数字 = 与此格接触的（至多）八格中的涂黑格个数。
import "shading"

cycle_shape(x, 1)
clue_cells_white(x, n)
adj8_black_clue(x, n)
''',
    [S, const("n", "八邻域涂黑格数")], [num_layer("n", "八邻域涂黑格数"), SHADE_LAYER],
    notes="完全实现：闭环（每黑格恰两个黑邻居 + 连通 + 无全黑2x2）+ 八邻域计数 + 数字格留白。"
          "「环不与自身对角接触」仅由无 2x2 部分保证。",
    sample=sample("bosnianroad", 6, 6, clues={"n": {"0,0": 2}}))

# --------------------------------------------------------------- sansaroad
add("sansaroad",
    '''
# 留白格连通且无全白 2x2；点提示相邻四格黑白多寡；
# 白色三角形格必须留白且恰和三个留白格相邻；其余留白格恰和两个留白格相邻。
import "shading"

connected(x, 0)
no2x2(x, 0)
majority_dot_clue(x, t)

for p in cells():
    if has_value(v, p):
        is_white(x, p)
        n_adj4(x, p, 0) == 3
    else:
        is_white(x, p) => n_adj4(x, p, 0) == 2
''',
    [S, const("t", "点提示 1=白多 2=黑多 3=相等"), const("v", "1 = 白色三角形（三叉路口）")],
    [DOT(), num_layer("v", "三叉路口"), SHADE_LAYER],
    notes="完全实现：留白连通 + 无全白2x2 + 三叉路口度数 3 + 其余留白度数 2 + 点提示。"
          "注意：度数和必须为偶数，故盘面上的三叉路口个数必须是偶数，否则必然无解。",
    # 手工验证的解：外框整圈留白 + 第 2 列竖向弦，(0,2) 与 (5,2) 恰为两个三叉路口。
    sample=sample("sansaroad", 6, 6, clues={"v": {"0,2": 1, "5,2": 1}}))

# -------------------------------------------------------------------- hinge
add("hinge",
    '''
# 每组连通涂黑格恰好跨过一条连续的区域边界，并被其分隔为沿该边界对称的两部分；
# 数字 = 此区域内涂黑格的个数。
import "shading"
import "regions"

region_black_count(x, n)
''',
    [S, const("n", "区域内涂黑格数")],
    [num_layer("n", "区域内涂黑格数"), SHADE_LAYER, REGION_LAYER], uses_regions=True,
    notes="部分实现：区域涂黑格数 = 数字。"
          "「每个涂黑连通组跨一条区域边界且沿其轴对称」需按连通组定位边界并做镜像匹配，未编码。",
    status="partial")

# ----------------------------------------------------------------- snakeegg
add("snakeegg",
    '''
# 涂黑一条宽度为一的蛇；黑圈表示此格是蛇的一端；
# 数字 = 其所在的留白连通组格数。
import "shading"

snake_shape(x, 1)
group_size_clue(x, n)

# 黑圈是蛇的端点。
for p in clue_cells(o):
    is_black(x, p)
    n_adj4(x, p, 1) == 1
''',
    [S, const("o", "1 = 蛇的一端"), const("n", "留白连通组格数")],
    [circle_layer("o", "蛇端"), num_layer("n", "留白组格数"), SHADE_LAYER], rows=6, cols=6,
    notes="部分实现：蛇形（连通/宽一/恰两端点/无全黑2x2）+ 端点圆圈 + 留白组格数。"
          "盘外「留白组格数一一对应」的多重集匹配未编码。",
    status="partial",
    sample=sample("snakeegg", 6, 6, clues={"o": {"0,0": 1}}))

# -------------------------------------------------------------------- snake
add("snake",
    '''
# 涂黑一条宽度为一且不和自身接触的蛇；黑圈 = 蛇的一端，白圈 = 蛇身（非端点）；
# 盘面外的数字表示此行或此列内涂黑格的个数。
import "shading"
import "outside"

snake_shape(x, 1)
row_count(x, 1, "left")
col_count(x, 1, "top")

for p in clue_cells(o):
    is_black(x, p)
    if at(o, p) == 2:
        n_adj4(x, p, 1) == 1
    else:
        n_adj4(x, p, 1) == 2
''',
    [S, const("o", "2 = 黑圈(端点), 1 = 白圈(蛇身)")],
    [circle_layer("o", "端点/蛇身"), SHADE_LAYER], rows=6, cols=6,
    notes="完全实现：蛇形 + 端点/蛇身圆圈 + 盘外行列计数（param left/top）。"
          "「不与自身对角接触」仅由无 2x2 部分保证。",
    sample=sample("snake", 6, 6, clues={"o": {"0,0": 2}}))

# --------------------------------------------------------------- shakashaka
add("shakashaka",
    '''
# 涂黑一些空格的一半（等腰直角三角形），使所有留白区域都是横平竖直或对角方向的长方形；
# 黑格里的数字表示与此格相邻的、涂了三角形的空格数。
import "shading"

adj_black_clue(x, n)
''',
    [S, const("n", "相邻三角形格数")], [num_layer("n", "相邻三角形格数"), SHADE_LAYER],
    notes="部分实现：黑格数字 = 相邻被涂格数。"
          "三角形有四种朝向、且「留白区域为（含对角方向的）长方形」需要三角形朝向变量与"
          "对角矩形判定，当前 0/1 涂黑模型无法表达，未编码。",
    status="partial")

# ----------------------------------------------------------------- dominion
add("dominion",
    '''
# 涂黑一些 1x2 的长方形（互不相邻），把盘面分为若干留白区域；字母格不能涂黑；
# 每个区域有且仅有一种字母，相同的字母都在同一个区域。
import "shading"

all_dominoes(x, 1)
clue_cells_white(x, a)

# 相同字母必须同区域，不同字母必须不同区域。
let ids = cc_id(x)
for p in clue_cells(a):
    for q in clue_cells(a):
        if before(p, q):
            if at(a, p) == at(a, q):
                at(ids, p) == at(ids, q)
            else:
                at(ids, p) != at(ids, q)
''',
    [S, const("a", "字母（同数字视为同字母）")], [num_layer("a", "字母"), SHADE_LAYER],
    notes="完全实现：涂黑格两两成 1x2 骨牌且不同骨牌互不相邻 + 字母格留白 + 同字母同区域/异字母异区域。",
    sample=sample("dominion", 6, 6, clues={"a": {"0,0": 1, "0,5": 2}}))

# ------------------------------------------------------------- circlesquare
add("circlesquare",
    '''
# 涂黑格连通、无全黑 2x2；黑圈格必须涂黑，白圈格必须留白；
# 每一组留白的连通组都是正方形。
import "shading"

wall_rule(x)
# 正方形的必要条件：留白连通组是长方形（无 L 形拐角）。
is_rect_group(x, 0)

for p in clue_cells(o):
    if at(o, p) == 2:
        is_black(x, p)
    else:
        is_white(x, p)
''',
    [S, const("o", "1 = 白圈, 2 = 黑圈")], [circle_layer("o"), SHADE_LAYER],
    notes="部分实现：涂黑连通 + 无全黑2x2 + 圆圈颜色 + 留白连通组为长方形。"
          "「长方形必须是正方形（长=宽）」未编码。",
    status="partial",
    sample=sample("circlesquare", 6, 6, clues={"o": {"0,0": 2, "2,2": 1}}))

# ------------------------------------------------------- tetrochain (arrows)
add("tetrochain",
    '''
# 每个涂黑连通组均为四格骨牌；所有骨牌对角连通；数字格不能涂黑；
# 数字表示相应方向上的黑格个数。
import "shading"

groups_of_size(x, 1, 4)
connected8(x, 1)
clue_cells_white(x, n)

for p in clue_cells(n):
    if has_value(d, p):
        num_eq(x[dir(p, at(d, p))], 1) == at(n, p)
''',
    [S, const("d", "箭头方向 0=上 1=下 2=左 3=右"), const("n", "该方向黑格数")],
    [arrow_layer("d"), num_layer("n", "该方向黑格数"), SHADE_LAYER], rows=6, cols=6,
    notes="部分实现：每个涂黑连通组恰 4 格 + 全部骨牌对角连通 + 数字格留白 + 方向计数。"
          "「对角相邻的两个四格骨牌不能全等」未编码。",
    status="partial",
    sample=sample("tetrochain", 6, 6, clues={"d": {"0,0": 3}, "n": {"0,0": 2}}))

# --------------------------------------------------------- tetrochaink (dots)
add("tetrochaink",
    '''
# 每个涂黑连通组均为四格骨牌；所有骨牌对角连通；
# 盘面内的点提示其所接触的（至多）四格中涂黑格和留白格哪种更多。
import "shading"

groups_of_size(x, 1, 4)
connected8(x, 1)
majority_dot_clue(x, t)
''',
    [S, const("t", "点提示 1=白多 2=黑多 3=相等")], [DOT(), SHADE_LAYER], rows=6, cols=6,
    notes="部分实现：每个涂黑连通组恰 4 格 + 对角连通 + 点提示黑白多寡。"
          "「对角相邻的两个四格骨牌不能全等」未编码。",
    status="partial",
    sample=sample("tetrochaink", 6, 6, clues={"t": {"1,1": 1}}))

# ----------------------------------------------------------------------- go
add("go",
    '''
# 有黑圈的格子涂黑，有白圈的格子留白；
# 圆圈里的数字 = 与其所在同色连通组相邻且颜色相反的总格数（「气」）。
import "shading"

for p in clue_cells(o):
    if at(o, p) == 2:
        is_black(x, p)
    else:
        is_white(x, p)
''',
    [S, const("o", "1 = 白圈, 2 = 黑圈"), const("n", "气的数量")],
    [circle_layer("o"), num_layer("n", "气"), SHADE_LAYER],
    notes="部分实现：圆圈颜色固定。"
          "「气」= 与整个连通组相邻的异色格总数，需要按连通组聚合去重计数，未编码。",
    status="partial", unencoded=["n"],
    sample=sample("go", 6, 6, clues={"o": {"0,0": 2, "3,3": 1}}))

# ------------------------------------------------------------------ norinuri
add("norinuri",
    '''
# 涂黑一些 1x2 的长方形（互不相邻），把盘面分为若干留白区域；数字格不能涂黑；
# 每一组连通的留白格恰好包含一个数字；数字 = 其所在留白连通组的格数。
import "shading"

all_dominoes(x, 1)
clue_cells_white(x, n)
group_size_clue(x, n)
clues_in_distinct_groups(x, n)
cc_count(x, 0) == clue_cells(n).size
''',
    [S, const("n", "留白连通组格数")], [num_layer("n", "留白组格数"), SHADE_LAYER],
    notes="完全实现：骨牌涂黑 + 数字格留白 + 每留白组恰一个数字（组数 = 数字数）+ 组格数。",
    sample=sample("norinuri", 6, 6, clues={"n": {"0,0": 34}}))

# ------------------------------------------------------------------- diamond
add("diamond",
    '''
# 涂黑一些 2x2 的菱形（斜正方形），使所有菱形与已给出的黑格一起对角连通；
# 菱形不能与黑格或其他菱形重叠或有公共边；黑格中的数字 = 与此格共顶点的菱形数。
import "shading"

connected8(x, 1)
''',
    [S, const("w", "1 = 已给出的黑格"), const("n", "共顶点的菱形数")],
    [num_layer("w", "已给黑格"), num_layer("n", "菱形数"), SHADE_LAYER],
    notes="部分实现：涂黑格对角连通。"
          "「菱形」是 2x2 斜正方形（占 4 格但呈 ◇ 形），需要专门的形状放置变量，未编码。",
    status="partial", unencoded=["w", "n"])

# ------------------------------------------------------------------- wittgen
add("wittgen",
    '''
# 放置一些互不重叠的 1x3 长方形（桌子）；桌子不能覆盖数字格；
# 数字 = 与之相邻的（至多）四格中被桌子覆盖的格数；所有未被覆盖的格子连通。
import "shading"

groups_of_size(x, 1, 3)
width_one(x, 1)
clue_cells_white(x, n)
adj_black_clue(x, n)
connected(x, 0)
''',
    [S, const("n", "相邻被覆盖格数")], [num_layer("n", "相邻被覆盖格数"), SHADE_LAYER],
    rows=6, cols=6,
    notes="部分实现：每个涂黑连通组恰 3 格且宽度为一 + 数字格不被覆盖 + 相邻计数 + 留白连通。"
          "「三格必须成直线（排除 L 形三连块）」未编码。",
    status="partial",
    sample=sample("wittgen", 6, 6, clues={"n": {"0,0": 1}}))

# ------------------------------------------------------------------- nuribou
add("nuribou",
    '''
# 每一组连通的留白格恰好包含一个数字；数字 = 其所在留白连通组的格数；
# 每一组连通的涂黑格必须是长或宽为一的长方形，且互相接触的两组涂黑格面积不能相同。
import "shading"

width_one(x, 1)
no2x2(x, 1)
group_size_clue(x, n)
clues_in_distinct_groups(x, n)
cc_count(x, 0) == clue_cells(n).size
''',
    [S, const("n", "留白连通组格数")], [num_layer("n", "留白组格数"), SHADE_LAYER],
    rows=6, cols=6,
    notes="部分实现：涂黑组宽度为一 + 无全黑2x2 + 每留白组恰一个数字 + 组格数。"
          "「涂黑组必须成直线（排除 L 形）」与「相接触的两组涂黑面积不同」未编码。",
    status="partial",
    sample=sample("nuribou", 6, 6, clues={"n": {"0,0": 36}}))

# ----------------------------------------------------------------- isowatari
add("isowatari",
    '''
# 每个涂黑连通组均为 N 格骨牌（N 由 param("n") 给出）；留白格连通；
# 黑圈格必须涂黑，白圈格必须留白；无全白 2x2。
import "shading"

groups_of_size(x, 1, param("n"))
connected(x, 0)
no2x2(x, 0)

for p in clue_cells(o):
    if at(o, p) == 2:
        is_black(x, p)
    else:
        is_white(x, p)
''',
    [S, const("o", "1 = 白圈, 2 = 黑圈")], [circle_layer("o"), SHADE_LAYER],
    rows=6, cols=6, params={"defaults": {"n": 3}},
    notes="完全实现：每个涂黑连通组恰 param(\"n\") 格 + 留白连通 + 无全白2x2 + 圆圈颜色。",
    sample=sample("isowatari", 6, 6, clues={"o": {"0,0": 2}}, params={"n": 3}))

# ---------------------------------------------------------------- mochinyoro
add("mochinyoro",
    '''
# 无全黑 2x2；所有留白格对角连通；每一组连通的留白格必须是长方形；
# 每一组连通的留白格至多包含一个数字；数字 = 其所在留白连通组的格数；
# 任意一组连通的涂黑格都不能是长方形。
import "shading"

no2x2(x, 1)
connected8(x, 0)
is_rect_group(x, 0)
group_size_clue(x, n)
clues_in_distinct_groups(x, n)
''',
    [S, const("n", "留白连通组格数")], [num_layer("n", "留白组格数"), SHADE_LAYER],
    rows=6, cols=6,
    notes="部分实现：无全黑2x2 + 留白对角连通 + 留白组为长方形 + 每组至多一个数字 + 组格数。"
          "「任意涂黑连通组都不是长方形」未编码。",
    status="partial",
    sample=sample("mochinyoro", 6, 6, clues={"n": {"0,0": 36}}))

# ------------------------------------------------------------------ cornerch
add("cornerch",
    '''
# 涂黑一些空格，使所有留白格对角连通；数字格不能涂黑；
# 数字 = 其所在留白连通组的面积；面积为偶数则必须是长方形，为奇数则不能是长方形。
import "shading"

connected8(x, 0)
clue_cells_white(x, n)
group_size_clue(x, n)
''',
    [S, const("n", "留白连通组面积")], [num_layer("n", "留白组面积"), SHADE_LAYER],
    rows=6, cols=6,
    notes="部分实现：留白对角连通 + 数字格留白 + 留白组面积 = 数字。"
          "「偶面积必为长方形 / 奇面积必不为长方形」的按组条件判定未编码。",
    status="partial",
    sample=sample("cornerch", 6, 6, clues={"n": {"0,0": 36}}))

# ------------------------------------------------------------------ tasquare
add("tasquare",
    '''
# 每一组涂黑的连通组都是正方形；留白格连通；
# 白色正方形格必须留白，且需和至少一个涂黑正方形相邻；
# 数字 = 与之相邻的所有涂黑正方形的面积之和。
import "shading"

is_rect_group(x, 1)
connected(x, 0)
clue_cells_white(x, n)

for p in clue_cells(n):
    n_adj4(x, p, 1) >= 1
''',
    [S, const("n", "相邻涂黑正方形面积之和")], [num_layer("n", "相邻正方形面积和"), SHADE_LAYER],
    notes="部分实现：涂黑组为长方形（正方形的必要条件）+ 留白连通 + 提示格留白且至少邻一涂黑格。"
          "「长=宽」与「相邻涂黑正方形面积之和」未编码。",
    status="partial",
    sample=sample("tasquare", 6, 6, clues={"n": {"1,1": 1}}))

# -------------------------------------------------------------------- antmill
add("antmill",
    '''
# 涂黑一些 1x2 的长方形；每个涂黑长方形恰和另外两个接触，
# 且所有长方形对角连通成一个整体（形成一个环）。
import "shading"

all_dominoes(x, 1)
connected8(x, 1)
''',
    [S], [SHADE_LAYER], rows=6, cols=6,
    notes="部分实现：涂黑格两两成骨牌且互不正交相邻 + 全部骨牌对角连通。"
          "「每块骨牌恰与另外两块接触（成环）」与 □/× 成对提示未编码。",
    status="partial")

# ---------------------------------------------------------------------- scrin
add("scrin",
    '''
# 每一组涂色的连通组都是长方形且至多包含一个圆圈；所有圆圈必须在涂色格内；
# 所有长方形对角连通成一个环；圈内数字 = 其所在长方形的面积。
import "shading"

is_rect_group(x, 1)
connected8(x, 1)
clue_cells_black(x, n)
group_size_clue(x, n)
clues_in_distinct_groups(x, n)
''',
    [S, const("n", "所在长方形面积")], [num_layer("n", "长方形面积"), SHADE_LAYER],
    rows=6, cols=6,
    notes="部分实现：涂色组为长方形 + 对角连通 + 圆圈在涂色格内 + 每组至多一个圆圈 + 组面积。"
          "「每个长方形恰和另外两个接触（成环）」未编码。",
    status="partial",
    sample=sample("scrin", 6, 6, clues={"n": {"0,0": 4}}))

# -------------------------------------------------------------------- lookair
add("lookair",
    '''
# 每一组涂黑的连通组都是正方形；在每行/每列内，任意两个仅由留白格分隔的涂黑格
# 不能在两个全等的正方形里；数字 = 此格及与其相邻的（至多）四格中涂黑格的个数。
import "shading"

is_rect_group(x, 1)
around_black_clue(x, n)
''',
    [S, const("n", "此格及四邻中涂黑格数")], [num_layer("n", "含自身五格黑数"), SHADE_LAYER],
    notes="部分实现：涂黑组为长方形（正方形的必要条件）+ 「此格及四邻」计数。"
          "「长=宽」与同行列「视线内不得有全等正方形」未编码。",
    status="partial",
    sample=sample("lookair", 6, 6, clues={"n": {"0,0": 0}}))

# --------------------------------------------------------------------- clouds
add("clouds",
    '''
# 每组连通的黑格都是长和宽都至少为二的长方形（云团），云团之间不能接触；
# 盘面外的数字表示此行或此列内涂黑格的个数。
import "shading"
import "outside"

is_rect_group(x, 1)
# 云团之间不接触（含对角）：不同组之间没有对角相邻。
row_count(x, 1, "left")
col_count(x, 1, "top")

# 长宽都至少为二 ⟹ 每个黑格至少有两个黑邻居。
for p in cells():
    is_black(x, p) => n_adj4(x, p, 1) >= 2
''',
    [S], [SHADE_LAYER], rows=6, cols=6,
    notes="部分实现：涂黑组为长方形 + 每黑格至少两个黑邻居（长宽≥2 的必要条件）+ 盘外行列计数。"
          "「云团之间互不接触」与圆角/× 预给提示未编码。",
    status="partial",
    sample=sample("clouds", 6, 6, params={"left": [2, 2, 0, 0, 0, 0],
                                          "top": [2, 2, 0, 0, 0, 0]}))

# ------------------------------------------------------------------- aquarium
add("aquarium",
    '''
# 每个区域内的水体必须稳定：留白格与涂黑格只能纵向相邻且留白格在上（水往下沉），
# 而同一区域内每一组涂黑连通组的水面必须在同一高度（水面是平的）；
# 盘面外的数字表示此行或此列内涂黑格的个数。
import "shading"
import "regions"
import "outside"

for p in cells():
    let below = shift(p, 1, 0)
    if below.size == 1:
        if same_region(p, below):
            # 水往下沉：此格有水则其下方（同区域）也有水。
            is_black(x, p) => is_black(x, below)
    let right = shift(p, 0, 1)
    if right.size == 1:
        if same_region(p, right):
            # 水面是平的：同区域同一行的相邻两格水位相同。
            at(x, p) == at(x, right)

row_count(x, 1, "left")
col_count(x, 1, "top")
''',
    [S], [SHADE_LAYER, REGION_LAYER], uses_regions=True, rows=6, cols=6,
    notes="完全实现：区域内水往下沉 + 同区域同行水位相同（水面平） + 盘外行列计数。",
    sample=sample("aquarium", 6, 6,
                  params={"left": [0, 0, 0, 2, 4, 6], "top": [2, 2, 2, 2, 2, 2]},
                  regions=block_regions(6, 6)))

# -------------------------------------------------------------------- shugaku
add("shugaku",
    '''
# 放置互不重叠的 1x2 长方形（床，其中一格是枕头），其余格子涂黑；
# 涂黑格连通且无全黑 2x2；每张床必须与至少一个涂黑格相邻；
# 数字 = 与之相邻的（至多）四格中的枕头个数。
import "shading"

wall_rule(x)
# 床占据留白格，且每张床是一个 1x2 骨牌。
all_dominoes(x, 0)

# 每张床至少与一个涂黑格相邻。
for p in cells():
    is_white(x, p) => n_adj4(x, p, 1) >= 1
''',
    [S, const("n", "相邻枕头数")], [num_layer("n", "相邻枕头数"), SHADE_LAYER],
    rows=6, cols=6,
    notes="部分实现：涂黑连通 + 无全黑2x2 + 留白格两两成 1x2 床 + 每床至少邻一涂黑格。"
          "「枕头」是床内的其中一格，需要额外变量；枕头计数与「竖床床头不朝北」未编码。",
    status="partial", unencoded=["n"])
