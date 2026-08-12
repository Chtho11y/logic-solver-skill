"""涂黑I — 颜色正交连通 (18 rules), authored one at a time from rules.txt."""
from gen import (add, const, shade_var, SHADE_LAYER, REGION_LAYER, num_layer,
                 circle_layer, arrow_layer, sample, block_regions)

S = shade_var()


# ---------------------------------------------------------------- disco
add("disco",
    '''
# 每个区域内涂黑恰好两组连通的格子；所有涂黑格连通；无全黑 2x2。
import "shading"

wall_rule(x)

# 「区域内恰好两组」的必要条件：每区域至少两个涂黑格。
for reg in regions:
    num_eq(x[reg], 1) >= 2
''',
    [S], [SHADE_LAYER, REGION_LAYER], uses_regions=True,
    notes="部分实现：涂黑连通 + 无全黑2x2 + 每区域至少2个涂黑格。"
          "「每区域恰好两组连通」需按区域计连通分量，当前 DSL 的 cc_count 只能全盘统计，未编码。",
    status="partial")

# ---------------------------------------------------------------- parquet
add("parquet",
    '''
# 涂黑格连通且不能形成回路（含 2x2）；每个粗线区域内完全涂黑恰好一个细线子区域。
import "shading"

# 连通且无环 ⟺ 树，这同时排除了 2x2 全黑。
color_is_tree(x, 1)
''',
    [S], [SHADE_LAYER, REGION_LAYER], uses_regions=True,
    notes="部分实现：涂黑格连通且无环（树）。"
          "「每个粗线区域内恰好整块涂黑一个细线子区域」需要两级区域（粗线+细线），"
          "题面模型只有一层区域，未编码。",
    status="partial")

# ---------------------------------------------------------------- nothree
add("nothree",
    '''
# 涂黑格互不相邻、留白连通；每个圆圈恰和一个涂黑格接触；
# 同一行或同一列的三个连续黑格不能等距排列。
import "shading"

island_rule(x)

for p in clue_cells(o):
    n_adj8(x, p, 1) == 1

no_equally_spaced_triple(x)

def no_equally_spaced_triple(x):
    for p in cells():
        for d in [1, 2, 3, 4, 5, 6, 7]:
            forbid_triple(x, p, shift(p, 0, d), shift(p, 0, 2 * d))
            forbid_triple(x, p, shift(p, d, 0), shift(p, 2 * d, 0))

def forbid_triple(x, p, q, r):
    if q.size == 1:
        if r.size == 1:
            not (is_black(x, p) and is_black(x, q) and is_black(x, r))
''',
    [S, const("o", "圆圈")], [circle_layer("o"), SHADE_LAYER],
    notes="完全实现（「接触」按含对角的八邻域解释）。",
    sample=sample("nothree", 6, 6, clues={"o": {"1,1": 1, "3,4": 1}}))

# ---------------------------------------------------------------- teri
add("teri",
    '''
# 涂黑格互不相邻、留白连通；白圈格必须留白；
# 白圈数字 = 包含此格的最大留白长方形面积。
import "shading"

island_rule(x)
clue_cells_white(x, n)
''',
    [S, const("n", "最大留白长方形面积")], [num_layer("n", "最大留白长方形面积"), SHADE_LAYER],
    notes="部分实现：island_rule + 白圈格留白。"
          "「包含此格的最大留白长方形面积」需对每个候选矩形取最大值，未编码。",
    status="partial")

# ---------------------------------------------------------------- akichi
add("akichi",
    '''
# 涂黑格互不相邻、留白连通；任一横段/纵段留白不得穿过两个以上区域边界；
# 数字 = 此区域内最大留白连通组的面积。
import "shading"
import "regions"

island_rule(x)
no_white_crossing_3_regions(x)
''',
    [S, const("n", "区域内最大留白连通组面积")],
    [num_layer("n", "区域内最大留白面积"), SHADE_LAYER, REGION_LAYER], uses_regions=True,
    notes="部分实现：island_rule + 留白段不穿过两个以上区域边界。"
          "「区域内最大留白连通组面积」需按区域求连通分量最大值，未编码。",
    status="partial", unencoded=["n"])

# ---------------------------------------------------------------- sumiwake
add("sumiwake",
    '''
# 涂黑格互不相邻、留白连通；任一横段/纵段留白不得穿过两个以上区域边界；
# 白圈恰和一个涂黑格接触，黑圈恰和两个涂黑格接触。
import "shading"
import "regions"

island_rule(x)
no_white_crossing_3_regions(x)

for p in clue_cells(o):
    if at(o, p) == 1:
        n_adj8(x, p, 1) == 1
    else:
        n_adj8(x, p, 1) == 2
''',
    [S, const("o", "1 = 白圈, 2 = 黑圈")], [circle_layer("o"), SHADE_LAYER, REGION_LAYER],
    uses_regions=True,
    notes="完全实现（「接触」按含对角的八邻域解释）。",
    sample=sample("sumiwake", 6, 6, clues={"o": {"1,1": 1}}, regions=block_regions(6, 6)))

# ---------------------------------------------------------------- usoone
add("usoone",
    '''
# 涂黑格互不相邻、留白连通；数字 = 相邻四格中涂黑格数；数字格不能涂黑；
# 每个区域内恰好有一个错误的数字。
import "shading"

island_rule(x)
clue_cells_white(x, n)

for reg in regions:
    wrong_clues_in(x, n, reg) == 1

def wrong_clues_in(x, n, reg):
    let total = 0
    for p in reg:
        if has_value(n, p):
            let total = total + b2i(n_adj4(x, p, 1) != at(n, p))
    return total
''',
    [S, const("n", "相邻涂黑格数（每区域恰有一个是错的）")],
    [num_layer("n", "相邻涂黑格数"), SHADE_LAYER, REGION_LAYER], uses_regions=True,
    notes="完全实现：含「每区域恰好一个错误数字」。",
    sample=sample("usoone", 4, 4,
                  clues={"n": {"0,0": 1, "0,2": 1, "2,0": 1, "2,2": 1}},
                  regions=block_regions(4, 4)))

# ---------------------------------------------------------------- yajikazu
add("yajikazu",
    '''
# 涂黑格互不相邻、留白连通；
# 留白格内带箭头的数字 = 从此格开始该方向的涂黑格数；
# 这些提示数若位于涂黑格内则不提供任何信息。
import "shading"

island_rule(x)

for p in clue_cells(n):
    if has_value(d, p):
        is_white(x, p) => num_eq(x[dir(p, at(d, p))], 1) == at(n, p)
''',
    [S, const("d", "箭头方向 0=上 1=下 2=左 3=右"), const("n", "该方向涂黑格数")],
    [arrow_layer("d"), num_layer("n", "该方向涂黑格数"), SHADE_LAYER],
    notes="完全实现：提示仅在其所在格留白时生效（涂黑时失效）。数字需与同格箭头方向成对给出。",
    sample=sample("yajikazu", 6, 6, clues={"d": {"0,0": 3}, "n": {"0,0": 2}}))

# ---------------------------------------------------------------- nuritwin
add("nuritwin",
    '''
# 每个区域内涂黑恰好两组连通格，两组面积相等且互不相邻；
# 所有涂黑格连通；无全黑 2x2；数字 = 其所在区域内一个涂黑连通组的面积。
import "shading"

wall_rule(x)

# 两组等面积 ⟹ 区域内涂黑格数为偶数且至少为 2。
for reg in regions:
    num_eq(x[reg], 1) >= 2
    num_eq(x[reg], 1) % 2 == 0

# 数字是「一组」的面积，故区域总涂黑数为其两倍。
for p in clue_cells(n):
    num_eq(x[region_of(p)], 1) == 2 * at(n, p)
''',
    [S, const("n", "区域内一个涂黑连通组的面积")],
    [num_layer("n", "一组涂黑格的面积"), SHADE_LAYER, REGION_LAYER], uses_regions=True,
    notes="部分实现：涂黑连通 + 无全黑2x2 + 区域涂黑数为偶且=2×数字。"
          "「恰好两组、两组全等面积且互不相邻」需按区域计连通分量，未编码。",
    status="partial")

# ---------------------------------------------------------------- guidearrow
add("guidearrow",
    '''
# 涂黑格互不相邻、留白连通；留白格不能形成回路（含 2x2）；
# 箭头表示从此格出发不经涂黑格、不倒退走到星星的唯一方向。
import "shading"

blacks_isolated(x)
# 留白连通且无环（这同时排除了全白 2x2）。
color_is_tree(x, 0)
''',
    [S, const("d", "箭头方向 0=上 1=下 2=左 3=右"), const("s", "1 = 星星")],
    [arrow_layer("d"), num_layer("s", "星星"), SHADE_LAYER],
    notes="部分实现：涂黑格互不相邻 + 留白连通且无环（树）。"
          "箭头「走到星星的唯一方向」涉及路径唯一性，未编码。",
    status="partial", unencoded=["d", "s"])

# ---------------------------------------------------------------- ayeheya
add("ayeheya",
    '''
# 涂黑格互不相邻、留白连通；任一横段/纵段留白不得穿过两个以上区域边界；
# 数字 = 此区域内涂黑格数；所有区域的涂黑情况必须 180° 旋转对称。
import "shading"
import "regions"

island_rule(x)
no_white_crossing_3_regions(x)
region_black_count(x, n)

for reg in regions:
    region_half_turn_symmetric(x, reg)

def region_half_turn_symmetric(x, reg):
    let minr = row_of(reg[0])
    let maxr = row_of(reg[0])
    let minc = col_of(reg[0])
    let maxc = col_of(reg[0])
    for p in reg:
        if row_of(p) < minr:
            let minr = row_of(p)
        if row_of(p) > maxr:
            let maxr = row_of(p)
        if col_of(p) < minc:
            let minc = col_of(p)
        if col_of(p) > maxc:
            let maxc = col_of(p)
    for p in reg:
        at(x, p) == at(x, cell(minr + maxr - row_of(p), minc + maxc - col_of(p)))
''',
    [S, const("n", "区域内涂黑格数")],
    [num_layer("n", "区域内涂黑格数"), SHADE_LAYER, REGION_LAYER], uses_regions=True,
    notes="完全实现：含区域 180° 旋转对称（绕区域外接框中心）。")

# ---------------------------------------------------------------- oasis
add("oasis",
    '''
# 涂黑格互不相邻、留白连通；无全白 2x2；白圈格必须留白；
# 白圈数字 = 从此格出发只经空白格可以走到的白圈个数。
import "shading"

island_rule(x)
no_white_2x2(x)
clue_cells_white(x, n)
''',
    [S, const("n", "可走到的白圈个数")], [num_layer("n", "可走到的白圈数"), SHADE_LAYER],
    notes="部分实现：island_rule + 无全白2x2 + 白圈格留白。"
          "「沿留白格可走到的白圈个数」是可达性计数，未编码。",
    status="partial")

# ---------------------------------------------------------------- sashikabe
add("sashikabe",
    '''
# 涂黑格连通、无全黑 2x2；每组连通留白必须是宽度为一的 L 形；
# 圆圈在 L 形的转弯处，箭头在一端指向转弯处；圆圈数字 = 留白区域面积。
import "shading"

wall_rule(x)
# 宽度为一：留白格最多两个留白邻居；同时排除全白 2x2。
width_one(x, 0)
no_white_2x2(x)
''',
    [S, const("n", "留白区域面积"), const("d", "箭头方向 0=上 1=下 2=左 3=右")],
    [num_layer("n", "留白区域面积"), arrow_layer("d"), SHADE_LAYER],
    notes="部分实现：涂黑连通 + 无全黑2x2 + 留白宽度为一。"
          "「恰好 L 形（仅一次转弯）」与圆圈/箭头定位、面积数字未编码。",
    status="partial", unencoded=["n", "d"])

# ---------------------------------------------------------------- oneroom
add("oneroom",
    '''
# 涂黑格互不相邻、留白连通；每个区域内的留白格也需连通；
# 数字 = 此区域内涂黑格数；任意两个相邻区域之间至多一对相邻留白格穿过边界。
import "shading"
import "regions"

island_rule(x)
region_black_count(x, n)

for ra in regions:
    for rb in regions:
        if region_id(ra[0]) < region_id(rb[0]):
            doors_between(x, ra, rb) <= 1

def doors_between(x, ra, rb):
    let rid = region_id(rb[0])
    let total = 0
    for p in ra:
        for q in adj4(p):
            if region_id(q) == rid:
                let total = total + b2i(is_white(x, p) and is_white(x, q))
    return total
''',
    [S, const("n", "区域内涂黑格数")],
    [num_layer("n", "区域内涂黑格数"), SHADE_LAYER, REGION_LAYER], uses_regions=True,
    notes="部分实现：island_rule + 区域涂黑数 + 相邻区域至多一扇门。"
          "「每个区域内部的留白也连通」需按区域求连通分量，未编码。",
    status="partial")

# ---------------------------------------------------------------- cts
add("cts",
    '''
# 涂黑格连通、无全黑 2x2；
# 盘面外的数字依次表示此行/此列中每一段连续涂黑格的长度。
import "shading"
import "outside"

wall_rule(x)
row_runs(x, "left")
col_runs(x, "top")
''',
    [S], [SHADE_LAYER],
    notes="部分实现：涂黑连通 + 无全黑2x2 + 盘外段长（param left/top，依次匹配）。"
          "问号「?」与星号「*」通配提示未编码。",
    status="partial",
    # 十字形：每行/列各一段，中央行列为整段 5。
    sample=sample("cts", 5, 5, params={"left": [[1], [1], [5], [1], [1]],
                                       "top": [[1], [1], [5], [1], [1]]}))

# ---------------------------------------------------------------- coral
add("coral",
    '''
# 涂黑格连通、无全黑 2x2；留白格连通到盘面边界；
# 盘面外的数字表示此行/此列中每段连续涂黑格的长度（无顺序要求）。
import "shading"

wall_rule(x)
# 留白必须能连到边界（注意是留白，不是涂黑）。
group_touches_border(x, 0)
''',
    [S], [SHADE_LAYER],
    notes="部分实现：涂黑连通 + 无全黑2x2 + 留白连通到边界。"
          "盘外「无序」段长集合需集合匹配（runs 只支持有序），未编码。",
    status="partial")

# ---------------------------------------------------------------- tapa
add("tapa",
    '''
# 涂黑格连通、无全黑 2x2；
# 格内一个或多个数字表示与此格接触的（至多）八格中所有连续涂黑段的长度（无序）。
import "shading"

wall_rule(x)
# 提示格自身永远不涂黑。
clue_cells_white(x, n)
''',
    [S, const("n", "八邻域连续涂黑段长度（可多个）")],
    [num_layer("n", "八邻域段长"), SHADE_LAYER],
    notes="部分实现：涂黑连通 + 无全黑2x2 + 提示格留白。"
          "Tapa 的环形八邻域多段长度（无序、支持问号）未编码。",
    status="partial")

# ---------------------------------------------------------------- nurimaze
add("nurimaze",
    '''
# 无全黑/全白 2x2；每个区域要么全部涂黑要么全部留白；
# 所有留白格连通且不成环（任两留白格之间存在唯一简单路径）；
# 圆圈在 S 到 G 的唯一路径上，三角形不在。
import "shading"
import "regions"

no_mono_2x2(x)
region_uniform(x)
# 连通且无环 ⟺ 树 ⟺ 任两格之间路径唯一。
color_is_tree(x, 0)
''',
    [S, const("m", "1 = S, 2 = G, 3 = 圆圈, 4 = 三角形")],
    [num_layer("m", "S/G/圆圈/三角"), SHADE_LAYER, REGION_LAYER], uses_regions=True,
    notes="部分实现：无单色2x2 + 区域单色 + 留白连通且无环（树）。"
          "圆圈/三角形相对 S–G 唯一路径的位置关系未编码。",
    status="partial", unencoded=["m"],
    # 区域取自一个手工验证过的解：留白呈「梳齿」（第 0 列为脊，偶数行为齿），
    # 其余奇数行的黑段各成一区。留白 21 格 / 相邻对 20 → 恰为树；
    # 偶数行全白使黑色无法凑出 2x2，奇数行仅第 0 列留白使白色也无 2x2。
    sample=sample("nurimaze", 6, 6,
                  regions={f"{r},{c}": (0 if (c == 0 or r % 2 == 0) else 1 + r // 2)
                           for r in range(6) for c in range(6)}))
