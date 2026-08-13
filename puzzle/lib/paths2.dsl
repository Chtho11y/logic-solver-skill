# ============================================================================
# paths2.dsl — helpers for 路径 I / 路径 II (open paths, bridges, ice).
#
#   import "paths2"
# ============================================================================

import "loops"


def no_outer_links(e):
    for p in cells():
        if shift(p, -1, 0).size == 0:
            link_up(e, p) == 0
        if shift(p, 1, 0).size == 0:
            link_down(e, p) == 0
        if shift(p, 0, -1).size == 0:
            link_left(e, p) == 0
        if shift(p, 0, 1).size == 0:
            link_right(e, p) == 0

def opposite_dir(d):
    if d == UP:
        return DOWN
    if d == DOWN:
        return UP
    if d == LEFT:
        return RIGHT
    return LEFT

def cell_idx(p):
    return row_of(p) * cols.size + col_of(p)

def ice_cell_ok(e, p):
    # 冰格：不经过 / 直行 / 十字自交（度数 4）
    return (cdeg(e, p) == 0) or (cdeg(e, p) == 2 and goes_straight(e, p)) or (cdeg(e, p) == 4)

def linked_same_x(e, x):
    for p in cells():
        for q in adj4(p):
            if before(p, q):
                link_between(e, p, q) == 1 => at(x, p) == at(x, q)

def wind_len(e, n, p, d):
    # Four Winds：从数字格 p 沿方向 d 连续占用的空格数（不含数字格）
    let total = 0
    let alive = link_dir(e, p, d) == 1
    for q in dir(p, d):
        if has_value(n, q):
            let alive = false
        let total = total + b2i(alive)
        let alive = alive and link_dir(e, q, d) == 1
    return total

def bridge_through(e, p):
    # 空格上的直桥：水平或竖直，两端边值相同且 > 0
    let horiz = link_left(e, p) > 0 and link_left(e, p) == link_right(e, p) and link_up(e, p) == 0 and link_down(e, p) == 0
    let vert = link_up(e, p) > 0 and link_up(e, p) == link_down(e, p) and link_left(e, p) == 0 and link_right(e, p) == 0
    return horiz or vert
