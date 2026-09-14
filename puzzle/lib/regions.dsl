# ============================================================================
# regions.dsl — templates for the 分区 family plus puzzles that read the
# pre-drawn regions of the board.
#
#   import "regions"
#
# Two different notions of “region” appear in this project:
#   * the *given* regions painted in the editor — available as the `regions`
#     constant and via `region_of(cell)` / `region_id(cell)`;
#   * a *solved* partition — a CC (region-partition) variable `c`, whose value
#     at each cell is that cell's region id, with `c.size` and `c.border`.
# ============================================================================

import "core"


# -- given regions ------------------------------------------------------------

def for_each_region_count(x, v, n):
    # Every given region contains exactly `n` cells holding `v`.
    for reg in regions:
        num_eq(x[reg], v) == n

def region_uniform(x):
    # 每个区域要么全部涂黑要么全部留白
    for reg in regions:
        num_eq(x[reg], 1) == 0 or num_eq(x[reg], 1) == reg.size

def cross_region_pairs(f):
    # Apply `f(p, q)` to every orthogonally adjacent pair of cells lying in
    # two different given regions.
    for p in cells():
        for q in adj4(p):
            if not same_region(p, q):
                f(p, q)

def in_region_count(x, p, v):
    # How many orthogonal neighbours of `p` inside p's own region hold `v`.
    let total = 0
    for q in adj4(p):
        if same_region(p, q):
            let total = total + b2i(at(x, q) == v)
    return total

def ordered_pairs_in(x, reg, v):
    # Ordered count of adjacent (p, q) pairs inside `reg` that both hold `v`;
    # a 4-cell set is connected iff this reaches 6.
    let total = 0
    for p in reg:
        for q in adj4(p):
            if same_region(p, q):
                let total = total + b2i(at(x, p) == v and at(x, q) == v)
    return total

def region_cells_in(w, rid):
    # The cells of window/region `w` that belong to given region `rid`.
    let out = []
    for p in w:
        if region_id(p) == rid:
            let out = out.append(p)
    return out

def no_white_crossing_3_regions(x):
    # 任意一横段或纵段留白格不能穿过两个以上区域边界
    # (Heyawake / Akichiwake / Ayeheya / Sumiwake)
    for p in cells():
        span_stops_at_3(x, p, RIGHT)
        span_stops_at_3(x, p, DOWN)

def span_stops_at_3(x, p, d):
    let seen = 1
    let last = region_id(p)
    let win = p
    for q in dir(p, d):
        if seen < 3:
            if region_id(q) != last:
                let seen = seen + 1
                let last = region_id(q)
            let win = win and q
            if seen == 3:
                num_eq(x[win], 1) >= 1

def count_in_region(f, reg):
    # Sum of `f(p)` (a 0/1 expression) over the cells of `reg`.
    let total = 0
    for p in reg:
        let total = total + b2i(f(p))
    return total


# -- solved partitions (CC variables) ----------------------------------------

def all_regions_size(c, n):
    # Every region of the partition has exactly `n` cells.
    for p in cells():
        at(c.size, p) == n

def region_size_clue(c, k):
    # 数字表示其所在区域的面积
    for p in clue_cells(k):
        at(c.size, p) == at(k, p)

def neighbour_sizes_differ(c):
    # 任意两个相邻的区域面积都不同 (Fillomino / Snake Pit / Wafusuma …)
    for p in cells():
        for q in adj4(p):
            at(c, p) != at(c, q) => at(c.size, p) != at(c.size, q)

def region_borders_drawn(c, b):
    # Copy the partition's border flags onto a 0/1 EDGE variable so the
    # front-end can draw them as thick lines.
    for e in edges():
        at(b, e) == at(c.border, e)

def one_clue_per_region(c, k):
    # 每个区域恰好包含一个提示格
    for p in cells():
        num_eq_cells_with_clue(c, k, p) == 1

def num_eq_cells_with_clue(c, k, p):
    let total = 0
    for q in clue_cells(k):
        let total = total + b2i(at(c, q) == at(c, p))
    return total

def at_most_one_clue_per_region(c, k):
    for p in cells():
        num_eq_cells_with_clue(c, k, p) <= 1


# -- rectangles inside a partition -------------------------------------------

def regions_are_rectangles(c):
    # Each region of the partition is an axis-aligned rectangle: no 2x2 window
    # may contain exactly three cells of one region.
    for w in slide(2, 2):
        for p in w:
            num_eq(c[w], at(c, p)) != 3

def region_width(c, p):
    # How many cells of p's region sit in p's row (the rectangle's width).
    let total = 0
    for q in row(row_of(p)):
        let total = total + b2i(at(c, q) == at(c, p))
    return total

def region_height(c, p):
    let total = 0
    for q in col(col_of(p)):
        let total = total + b2i(at(c, q) == at(c, p))
    return total

def regions_are_squares(c):
    regions_are_rectangles(c)
    for p in cells():
        region_width(c, p) == region_height(c, p)

def no_four_regions_at_vertex(c):
    # 任意顶点不能同时是四个不同区域的一角
    for p in cells():
        let q = shift(p, 0, 1)
        let s = shift(p, 1, 0)
        let t = shift(p, 1, 1)
        if q.size == 1:
            if s.size == 1:
                if t.size == 1:
                    at(c, p) == at(c, q) or at(c, p) == at(c, s) or at(c, p) == at(c, t) or at(c, q) == at(c, s) or at(c, q) == at(c, t) or at(c, s) == at(c, t)

def region_180_symmetric(c):
    # 每个区域绕自身质心 180° 对称：p 在区域内 ⇒ 2*centroid - p 也在区域内。
    for p in cells():
        let sr = 0
        let sc = 0
        for t in cells():
            let sr = sr + b2i(at(c, t) == at(c, p)) * row_of(t)
            let sc = sc + b2i(at(c, t) == at(c, p)) * col_of(t)
        let n = at(c.size, p)
        let ok = 0
        for t in cells():
            let ok = ok + b2i(at(c, t) == at(c, p) and n * row_of(t) + n * row_of(p) == sr + sr and n * col_of(t) + n * col_of(p) == sc + sc)
        ok == 1
