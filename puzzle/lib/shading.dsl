# ============================================================================
# shading.dsl — templates for the “涂黑” families (categories 涂黑 I / II / III).
#
#   import "shading"
#
# `x` is always a 0/1 cell variable: 1 = black, 0 = white.
# ============================================================================

import "core"


# -- the three classic global shapes -----------------------------------------

def black_connected(x):
    # 所有涂黑的格子连通成一个整体
    connected(x, 1)

def white_connected(x):
    # 留白的格子连通成一个整体
    connected(x, 0)

def blacks_isolated(x):
    # 涂黑的格子之间不相邻
    no_adjacent(x, 1)

def no_black_2x2(x):
    # 没有全部涂黑的 2x2 结构
    no2x2(x, 1)

def no_white_2x2(x):
    # 没有全部留白的 2x2 结构
    no2x2(x, 0)

def no_mono_2x2(x):
    # 没有全部涂黑或者全部留白的 2x2 结构
    no2x2(x, 1)
    no2x2(x, 0)


# The two most reused whole-puzzle skeletons ---------------------------------

def island_rule(x):
    # “涂黑格互不相邻 + 留白连通” (Hitori / Kurodoko / Heyawake / Nurimisaki …)
    blacks_isolated(x)
    white_connected(x)

def wall_rule(x):
    # “涂黑格连通 + 无 2x2 全黑” (Nurikabe / Aqre / Canal View / Tapa …)
    black_connected(x)
    no_black_2x2(x)


# -- clue helpers -------------------------------------------------------------

def adj_black_clue(x, c):
    # 数字表示与之相邻的（至多）四格中涂黑格的个数
    for p in clue_cells(c):
        n_adj4(x, p, 1) == at(c, p)

def around_black_clue(x, c):
    # 数字表示此格及与其相邻的（至多）四格中涂黑格的个数
    for p in clue_cells(c):
        n_around(x, p, 1) == at(c, p)

def adj8_black_clue(x, c):
    # 数字表示与此格接触的（至多）八格中涂黑格的个数
    for p in clue_cells(c):
        n_adj8(x, p, 1) == at(c, p)

def clue_cells_white(x, c):
    # 数字格不能涂黑
    for p in clue_cells(c):
        is_white(x, p)

def clue_cells_black(x, c):
    for p in clue_cells(c):
        is_black(x, p)

def region_black_count(x, c):
    # 数字表示此区域内涂黑格的个数（提示写在区域内任意一格）
    for p in clue_cells(c):
        num_eq(x[region_of(p)], 1) == at(c, p)

def region_black_exact(x, reg, n):
    num_eq(x[reg], 1) == n


# -- line-of-sight helpers ----------------------------------------------------

def see_count(x, p, d, v):
    # How many consecutive cells holding `v` start right next to `p` in
    # direction `d` before the first cell of the opposite colour.
    let ray = dir(p, d)
    let total = 0
    let blocked = false
    for q in ray:
        let hit = at(x, q) == v
        let total = total + b2i(hit and not blocked)
        let blocked = blocked or not hit
    return total

def see4(x, p, v):
    # Cells of colour `v` visible from `p` in the four orthogonal directions
    # (excluding `p` itself).
    return see_count(x, p, UP, v) + see_count(x, p, DOWN, v) + see_count(x, p, LEFT, v) + see_count(x, p, RIGHT, v)


# -- reachability -------------------------------------------------------------

def group_touches_border(x, v):
    # Every cell holding `v` belongs to a group that reaches the board edge
    # (Cave: 涂黑格必须能沿涂黑格连通到盘面边界).
    let ids = cc_id(x)
    for p in cells():
        let ok = false
        for b in boundary():
            let ok = ok or (at(x, b) == v and at(ids, b) == at(ids, p))
        eq(x, p, v) => ok

def clues_in_distinct_groups(x, c):
    # 每一组连通格至多包含一个数字
    let ids = cc_id(x)
    for p in clue_cells(c):
        for q in clue_cells(c):
            if before(p, q):
                at(ids, p) != at(ids, q)
