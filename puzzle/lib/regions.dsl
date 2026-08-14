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
    return count_where(adj4(p), fn (q) -> same_region(p, q) and at(x, q) == v)

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
    return count_where(reg, fn (p) -> f(p) == 1)


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
    return count_where(clue_cells(k), fn (q) -> at(c, q) == at(c, p))

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
    # Same-row occupancy; equals bbox width only for rectangles.
    return cc_line_count(c, p, 0)

def region_height(c, p):
    return cc_line_count(c, p, 1)

def regions_are_squares(c):
    regions_are_rectangles(c)
    for p in cells():
        region_width(c, p) == region_height(c, p)

def no_four_meet(c):
    # No lattice vertex is a corner of four distinct regions (a 2x2 of 4 ids).
    for w in slide(2, 2):
        let shared = false
        for p in w:
            for q in w:
                if before(p, q):
                    let shared = shared or (at(c, p) == at(c, q))
        shared

def region_border_clue(c, k):
    # 数字 = 此格四边中属于区域边界的边数（盘面外缘也算边界）
    for p in clue_cells(k):
        num_eq(c.border[edge_of(p)], 1) == at(k, p)

def region_deg(c, p):
    return at(c.deg, p)

def same_reg_dir(c, p, d):
    if not in_grid(p, dr_of(d), dc_of(d)):
        return false
    return at(c, step(p, d)) == at(c, p)

def region_notch_count(c, p):
    return cc_notch_count(c, p)

def region_end_count(c, p):
    return cc_deg_count(c, p, 1)

def region_above(c, p):
    return cc_half_count(c, p, 0, 0)

def region_below(c, p):
    return cc_half_count(c, p, 0, 1)

def region_left_of(c, p):
    return cc_half_count(c, p, 1, 0)

def region_right_of(c, p):
    return cc_half_count(c, p, 1, 1)
