# bonsan — 木头人
# 圆圈直线滑动；落点盘面中心对称。数字 = 移动距离（0 不能动）。

import "paths2"

no_outer_links(e)
linked_same_x(e, x)

for p in cells():
    if has_value(o, p):
        at(x, p) == cell_idx(p) + 1
        cdeg(e, p) == 0 or cdeg(e, p) == 1
    else:
        (at(x, p) == 0 and cdeg(e, p) == 0) or (at(x, p) != 0 and (cdeg(e, p) == 1 or cdeg(e, p) == 2))
        cdeg(e, p) == 2 => goes_straight(e, p)

for p in clue_cells(o):
    cc_count(x, at(x, p)) == 1
    let tips = 0
    let sz = 0
    for q in cells():
        let tips = tips + b2i(at(x, q) == at(x, p) and cdeg(e, q) <= 1)
        let sz = sz + b2i(at(x, q) == at(x, p))
    (cdeg(e, p) == 0 and tips == 1) or (cdeg(e, p) == 1 and tips == 2)
    if has_value(n, p):
        sz == at(n, p) + 1

for q in cells():
    let dest = false
    for p in clue_cells(o):
        let is_dest = false
        if row_of(q) == row_of(p) and col_of(q) == col_of(p):
            let is_dest = cdeg(e, p) == 0
        else:
            let is_dest = cdeg(e, p) == 1 and at(x, q) == at(x, p) and cdeg(e, q) == 1
        let dest = dest or is_dest
    at(f, q) == b2i(dest)

for p in cells():
    let q = cell(rows.size - 1 - row_of(p), cols.size - 1 - col_of(p))
    at(f, p) == at(f, q)
