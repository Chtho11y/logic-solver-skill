# ============================================================================
# loops.dsl — templates for loop / path puzzles (categories 回路 I·II, 路径 I·II).
#
#   import "loops"
#
# Two lattices are available:
#   * `loop(e)`  — `e` is a 0/1 EDGE variable and the drawn segments run along
#     cell boundaries (Slitherlink family). Degrees are counted at corners.
#   * `cloop(e)` — the segments join adjacent cell centres (Masyu family). The
#     edge separating two cells stands for the link between them, so an "H"
#     edge is a vertical link and a "V" edge a horizontal one.
# ============================================================================

import "core"


# -- the four links leaving a cell -------------------------------------------

def up_edge(p):
    return edge("H", row_of(p), col_of(p))

def down_edge(p):
    return edge("H", row_of(p) + 1, col_of(p))

def left_edge(p):
    return edge("V", row_of(p), col_of(p))

def right_edge(p):
    return edge("V", row_of(p), col_of(p) + 1)

def link_up(e, p):
    return at(e, up_edge(p))

def link_down(e, p):
    return at(e, down_edge(p))

def link_left(e, p):
    return at(e, left_edge(p))

def link_right(e, p):
    return at(e, right_edge(p))


# -- how the loop crosses a cell ---------------------------------------------

def on_loop(e, p):
    # 回路经过此格
    return cdeg(e, p) == 2

def off_loop(e, p):
    # 回路不经过此格
    return cdeg(e, p) == 0

def goes_straight(e, p):
    # 回路笔直穿过此格
    return (link_up(e, p) + link_down(e, p) == 2) or (link_left(e, p) + link_right(e, p) == 2)

def goes_horizontal(e, p):
    return link_left(e, p) + link_right(e, p) == 2

def goes_vertical(e, p):
    return link_up(e, p) + link_down(e, p) == 2

def turns(e, p):
    # 回路在此格转弯
    return on_loop(e, p) and not goes_straight(e, p)

def link_dir(e, p, d):
    if d == UP:
        return link_up(e, p)
    if d == DOWN:
        return link_down(e, p)
    if d == LEFT:
        return link_left(e, p)
    return link_right(e, p)

def link_between(e, p, q):
    # The link variable joining two orthogonally adjacent cells.
    if row_of(p) == row_of(q):
        if col_of(q) > col_of(p):
            return at(e, edge("V", row_of(p), col_of(q)))
        return at(e, edge("V", row_of(p), col_of(p)))
    if row_of(q) > row_of(p):
        return at(e, edge("H", row_of(q), col_of(p)))
    return at(e, edge("H", row_of(p), col_of(p)))

def straight_beside(e, p, d):
    let q = step(p, d)
    if q.size == 0:
        return false
    return on_loop(e, q) and goes_straight(e, q)

def turn_beside(e, p, d):
    let q = step(p, d)
    if q.size == 0:
        return false
    return turns(e, q)

def full_loop(e):
    # 回路经过所有格子
    cloop(e)
    for p in cells():
        on_loop(e, p)

def loop_visits_all_but(e, x):
    # 回路经过所有未涂黑的格子（Yajilin / Koburin 家族），x 为 0/1 涂黑变量
    cloop(e)
    for p in cells():
        on_loop(e, p) == (at(x, p) == 0)


# -- straight-segment lengths -------------------------------------------------

def seg_len(e, p, d):
    # Number of consecutive cells the loop keeps travelling through from `p`
    # in direction `d` (excluding `p`), stopping as soon as it turns or stops.
    let total = 0
    let alive = true
    for q in dir(p, d):
        let straight = on_loop(e, q) and goes_straight(e, q)
        let total = total + b2i(alive and on_loop(e, q))
        let alive = alive and straight
    return total

def arm_len(e, p, d):
    # Length of the straight arm of the loop leaving `p` towards `d`.
    let total = 0
    let alive = true
    for q in dir(p, d):
        let total = total + b2i(alive and on_loop(e, q))
        let alive = alive and on_loop(e, q) and goes_straight(e, q)
    return total


# -- Slitherlink-style loops on the corner lattice ---------------------------

def cell_edge_count(e, p):
    # How many of the four boundary edges of cell `p` carry the loop.
    return link_up(e, p) + link_down(e, p) + link_left(e, p) + link_right(e, p)

def inside_flag(e, ins):
    # `ins` is a 0/1 cell variable that is 1 exactly for cells enclosed by the
    # corner-lattice loop `e`: parity flips whenever a loop edge is crossed.
    for p in cells():
        let up = shift(p, -1, 0)
        if up.size == 0:
            at(ins, p) == link_up(e, p)
        else:
            (at(ins, p) != at(ins, up)) == (link_up(e, p) == 1)


# -- regions visited by a cell loop ------------------------------------------

def region_crossings(e, reg):
    # How many links leave `reg` — a loop entering it k times crosses 2k links.
    let total = 0
    for p in reg:
        for q in adj4(p):
            if not same_region(p, q):
                let total = total + link_between(e, p, q)
    return total

def region_visited_cells(e, reg):
    let total = 0
    for p in reg:
        let total = total + b2i(on_loop(e, p))
    return total

def region_turns(e, reg):
    let total = 0
    for p in reg:
        let total = total + b2i(turns(e, p))
    return total

def nearest_loop_dist(e, p, d):
    # 1-based distance to the nearest loop edge looking from `p` in direction
    # `d` (the far side of `p`, then of each cell beyond). 0 = none.
    let dist = 0
    let seen = false
    let hit0 = link_dir(e, p, d) == 1
    let dist = ite(hit0, 1, dist)
    let seen = seen or hit0
    let k = 1
    for q in dir(p, d):
        let k = k + 1
        let hit = link_dir(e, q, d) == 1
        let dist = ite(seen, dist, ite(hit, k, dist))
        let seen = seen or hit
    return dist

def arm_used_len(e, p, d):
    # Straight-arm length including `p` itself, or 0 if the loop does not leave `p` that way.
    return ite(link_dir(e, p, d) == 1, 1 + arm_len(e, p, d), 0)

def full_straight_len(e, p):
    return 1 + ite(goes_horizontal(e, p), arm_len(e, p, LEFT) + arm_len(e, p, RIGHT), arm_len(e, p, UP) + arm_len(e, p, DOWN))
