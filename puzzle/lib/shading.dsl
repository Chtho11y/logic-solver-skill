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

def nb_bit(x, p, dr, dc):
    return nb_at(x, p, dr, dc)

def around8_shade_bits(x, p):
    # Clockwise 8-neighbourhood occupancy, missing cells count as 0.
    return [nb_bit(x, p, -1, 0), nb_bit(x, p, -1, 1), nb_bit(x, p, 0, 1), nb_bit(x, p, 1, 1), nb_bit(x, p, 1, 0), nb_bit(x, p, 1, -1), nb_bit(x, p, 0, -1), nb_bit(x, p, -1, -1)]

def clue_lengths4(n, n2, n3, n4, p):
    let lens = [at(n, p)]
    if has_value(n2, p):
        let lens = lens and [at(n2, p)]
    if has_value(n3, p):
        let lens = lens and [at(n3, p)]
    if has_value(n4, p):
        let lens = lens and [at(n4, p)]
    return lens

def tapa_clue(x, n, n2, n3, n4, p):
    let bits = around8_shade_bits(x, p)
    if not has_value(n2, p) and at(n, p) < 0:
        runs_cycle(bits, 0) or runs_cycle(bits, 0 - 1)
    else:
        runs_cycle(bits, clue_lengths4(n, n2, n3, n4, p))

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


# -- acyclicity ---------------------------------------------------------------

def color_count(x, v):
    return count_where(cells(), fn (p) -> eq(x, p, v))

def color_adjacent_pairs(x, v):
    # Unordered count of orthogonally adjacent pairs both holding `v`.
    let total = 0
    for p in cells():
        let right = shift(p, 0, 1)
        if right.size == 1:
            let total = total + b2i(eq(x, p, v) and eq(x, right, v))
        let down = shift(p, 1, 0)
        if down.size == 1:
            let total = total + b2i(eq(x, p, v) and eq(x, down, v))
    return total

def color_is_tree(x, v):
    # `v`-cells are connected AND contain no cycle (so no 2x2 block either):
    # a connected graph is a tree exactly when |V| - |E| == 1.
    connected(x, v)
    color_count(x, v) - color_adjacent_pairs(x, v) == 1

def color_is_acyclic(x, v):
    # No cycle, without forcing connectivity: |V| - |E| == #components.
    color_count(x, v) - color_adjacent_pairs(x, v) == cc_count(x, v)

def width_one(x, v):
    # Every `v`-cell has at most two `v`-neighbours (a width-1 path/snake).
    for p in cells():
        eq(x, p, v) => n_adj4(x, p, v) <= 2


# -- shapes made of same-coloured cells ---------------------------------------

def endpoint_count(x, v):
    # How many `v`-cells have exactly one `v`-neighbour (path ends).
    let total = 0
    for p in cells():
        let total = total + b2i(eq(x, p, v) and n_adj4(x, p, v) == 1)
    return total

def snake_shape(x, v):
    # 一条宽度为一、正交连通、恰有两个端点的蛇。
    connected(x, v)
    no2x2(x, v)
    width_one(x, v)
    endpoint_count(x, v) == 2

def cycle_shape(x, v):
    # `v` 格构成一条宽度为一的闭合环（每格恰两个同色邻居）。
    connected(x, v)
    no2x2(x, v)
    for p in cells():
        eq(x, p, v) => n_adj4(x, p, v) == 2

def all_dominoes(x, v):
    # `v` 格两两配对成 1x2 骨牌；每格恰有一个同色邻居，
    # 这同时保证了不同骨牌之间互不正交相邻。
    for p in cells():
        eq(x, p, v) => n_adj4(x, p, v) == 1

def square_groups(x, v):
    # Every `v` 4-component is a square (filled bounding box, width == height).
    let w = cc_width(x)
    let h = cc_height(x)
    for p in cells():
        eq(x, p, v) => cc_is_rect(x, p) and at(w, p) == at(h, p)

def straight_groups(x, v):
    # Every `v` 4-component is a straight bar (bounding box width or height is 1).
    let w = cc_width(x)
    let h = cc_height(x)
    for p in cells():
        eq(x, p, v) => at(w, p) == 1 or at(h, p) == 1

def groups_of_size(x, v, k):
    # 每一组连通的 `v` 格恰好 k 格。
    let sz = cc_size(x)
    for p in cells():
        eq(x, p, v) => at(sz, p) == k

def group_size_clue(x, c):
    # 数字 = 其所在同色连通组的格数。
    let sz = cc_size(x)
    for p in clue_cells(c):
        at(sz, p) == at(c, p)

def group8_size_clue(x, c):
    let sz = cc8_size(x)
    for p in clue_cells(c):
        at(sz, p) == at(c, p)

def majority_dot_clue(x, c):
    # 盘面内的点提示其所接触的（至多）四格中涂黑格和留白格哪种更多：
    # 1 = 留白更多, 2 = 涂黑更多, 3 = 一样多。
    for p in clue_cells(c):
        if at(c, p) == 1:
            n_adj4(x, p, 0) > n_adj4(x, p, 1)
        elif at(c, p) == 2:
            n_adj4(x, p, 1) > n_adj4(x, p, 0)
        else:
            n_adj4(x, p, 1) == n_adj4(x, p, 0)


# -- region-scoped black groups (涂黑III) ------------------------------------

def region_blacks_separated(x):
    # 涂黑格不能隔着区域边界相邻
    for p in cells():
        for q in adj4(p):
            if not same_region(p, q):
                not (is_black(x, p) and is_black(x, q))

def one_black_group_per_region(x):
    # 每个区域恰好一组连通的涂黑格（组不跨区 + 组数 = 区域数）
    region_blacks_separated(x)
    cc_count(x, 1) == regions.size

def at_most_one_black_group_per_region(x):
    region_blacks_separated(x)
    for p in cells():
        for q in cells():
            if before(p, q):
                if same_region(p, q):
                    not (cc_root(x, p) and cc_root(x, q) and is_black(x, p) and is_black(x, q))

def two_black_groups_per_region(x):
    region_blacks_separated(x)
    cc_count(x, 1) == 2 * regions.size
    for p in cells():
        let nroot = 0
        for q in region_of(p):
            let nroot = nroot + b2i(cc_root(x, q) and is_black(x, q))
        nroot == 2

def half_filled_lines(x):
    # 每行每列恰一半涂黑（盘面边长须为偶数）
    for r in rows:
        num_eq(x[r], 1) == cols.size / 2
    for c in cols:
        num_eq(x[c], 1) == rows.size / 2

def lines_all_unique(x):
    # 任意两行（两列）的涂黑图案不同
    for p in cells():
        for q in cells():
            if col_of(p) == 0 and col_of(q) == 0 and row_of(p) < row_of(q):
                let diff = false
                for a in row(row_of(p)):
                    for b in row(row_of(q)):
                        if col_of(a) == col_of(b):
                            let diff = diff or (at(x, a) != at(x, b))
                diff
    for p in cells():
        for q in cells():
            if row_of(p) == 0 and row_of(q) == 0 and col_of(p) < col_of(q):
                let diff = false
                for a in col(col_of(p)):
                    for b in col(col_of(q)):
                        if row_of(a) == row_of(b):
                            let diff = diff or (at(x, a) != at(x, b))
                diff
