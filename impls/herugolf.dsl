# herugolf — 高尔夫
# 每球经递减长度的直线杆到达唯一 H。停点不在水上；不可 180° 掉头。路径不交叉。

import "paths2"

no_outer_links(e)
linked_same_x(e, u)

for p in cells():
    if has_value(o, p):
        at(u, p) == cell_idx(p) + 1
        at(x, p) == 1
        at(r, p) == at(n, p)
        at(s, p) == at(n, p)
        cdeg(e, p) == 1
        at(n, p) >= 1
    elif has_value(h, p):
        (at(u, p) == 0 and at(x, p) == 0 and cdeg(e, p) == 0) or (at(u, p) != 0 and at(x, p) >= 2 and cdeg(e, p) == 1 and at(r, p) == 0)
    else:
        (at(u, p) == 0 and at(x, p) == 0 and cdeg(e, p) == 0 and at(r, p) == 0 and at(s, p) == 0) or (at(u, p) != 0 and at(x, p) >= 2 and cdeg(e, p) == 2)

for p in clue_cells(o):
    cc_count(u, at(u, p)) == 1
    let nh = 0
    for q in clue_cells(h):
        let nh = nh + b2i(at(u, q) == at(u, p))
    nh == 1

for p in cells():
    if has_value(w, p):
        at(r, p) != 0 or at(u, p) == 0

for p in cells():
    for q in adj4(p):
        if before(p, q):
            link_between(e, p, q) == 1 => abs(at(x, p) - at(x, q)) == 1

for p in cells():
    at(x, p) >= 2 => has_pred(e, x, p)
    at(r, p) > 0 => has_succ_same(e, x, r, s, p)
    at(r, p) == 0 and at(u, p) != 0 and not has_value(h, p) => has_succ_new(e, x, r, s, p)
    at(r, p) > 0 and at(r, p) < at(s, p) => goes_straight(e, p)

def has_pred(e, x, p):
    let ok = false
    for q in adj4(p):
        let ok = ok or (link_between(e, p, q) == 1 and at(x, q) == at(x, p) - 1)
    return ok

def has_succ_same(e, x, r, s, p):
    let ok = false
    for q in adj4(p):
        let ok = ok or (link_between(e, p, q) == 1 and at(x, q) == at(x, p) + 1 and at(r, q) == at(r, p) - 1 and at(s, q) == at(s, p))
    return ok

def has_succ_new(e, x, r, s, p):
    let ok = false
    for q in adj4(p):
        let rev = false
        for t in adj4(p):
            let rev = rev or (link_between(e, p, t) == 1 and at(x, t) == at(x, p) - 1 and row_of(t) - row_of(p) == row_of(p) - row_of(q) and col_of(t) - col_of(p) == col_of(p) - col_of(q))
        let ok = ok or (link_between(e, p, q) == 1 and at(x, q) == at(x, p) + 1 and at(s, q) == at(s, p) - 1 and at(r, q) == at(s, q) and at(s, q) >= 1 and not rev)
    return ok
