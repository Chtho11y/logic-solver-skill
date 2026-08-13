# coffeemilk — 咖啡牛奶
# 圆圈之间直连，不交叉、不穿圈；黑白不能直接相连。
# 每一连通组恰好一个灰圈，且黑圈数等于白圈数。

import "paths2"

no_outer_links(e)
linked_same_x(e, u)

for p in cells():
    if has_value(o, p):
        at(u, p) != 0
    else:
        (cdeg(e, p) == 0 and at(u, p) == 0) or (cdeg(e, p) == 2 and goes_straight(e, p) and at(u, p) != 0)

for p in clue_cells(o):
    if at(o, p) == 3:
        at(u, p) == cell_idx(p) + 1
        let blacks = 0
        let whites = 0
        let grays = 0
        for q in clue_cells(o):
            let same = at(u, p) == at(u, q)
            let whites = whites + b2i(same and at(o, q) == 1)
            let blacks = blacks + b2i(same and at(o, q) == 2)
            let grays = grays + b2i(same and at(o, q) == 3)
        grays == 1
        blacks == whites
    else:
        let hit = false
        for q in clue_cells(o):
            if at(o, q) == 3:
                let hit = hit or (at(u, p) == at(u, q))
        hit

for p in clue_cells(o):
    for q in clue_cells(o):
        if before(p, q):
            if (at(o, p) == 1 and at(o, q) == 2) or (at(o, p) == 2 and at(o, q) == 1):
                no_direct_bridge(e, o, p, q)

for p in clue_cells(o):
    cc_count(u, at(u, p)) == 1

def no_direct_bridge(e, o, p, q):
    if row_of(p) == row_of(q):
        if col_of(q) > col_of(p):
            forbid_full_segment(e, o, p, q, RIGHT)
        else:
            forbid_full_segment(e, o, p, q, LEFT)
    elif col_of(p) == col_of(q):
        if row_of(q) > row_of(p):
            forbid_full_segment(e, o, p, q, DOWN)
        else:
            forbid_full_segment(e, o, p, q, UP)
    else:
        true

def forbid_full_segment(e, o, p, q, d):
    let blocked = false
    let alln = true
    let prev = p
    let active = true
    for r in dir(p, d):
        if active:
            if has_value(o, r) and not (row_of(r) == row_of(q) and col_of(r) == col_of(q)):
                let blocked = true
            let alln = alln and (link_between(e, prev, r) == 1)
            let prev = r
            if row_of(r) == row_of(q) and col_of(r) == col_of(q):
                let active = false
    not blocked => not alln
