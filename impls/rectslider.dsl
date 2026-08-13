# rectslider — 长方滑动
# 黑格直线滑动；落点每一连通组都是面积至少为 2 的长方形。数字 = 移动距离。

import "paths2"

no_outer_links(e)
linked_same_x(e, x)

for p in cells():
    if has_value(b, p):
        at(x, p) == cell_idx(p) + 1
        cdeg(e, p) == 0 or cdeg(e, p) == 1
    else:
        (at(x, p) == 0 and cdeg(e, p) == 0) or (at(x, p) != 0 and (cdeg(e, p) == 1 or cdeg(e, p) == 2))
        cdeg(e, p) == 2 => goes_straight(e, p)

for p in clue_cells(b):
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
    for p in clue_cells(b):
        let is_dest = false
        if row_of(q) == row_of(p) and col_of(q) == col_of(p):
            let is_dest = cdeg(e, p) == 0
        else:
            let is_dest = cdeg(e, p) == 1 and at(x, q) == at(x, p) and cdeg(e, q) == 1
        let dest = dest or is_dest
    at(f, q) == b2i(dest)

is_rect_group(f, 1)
let szf = cc_size(f)
for p in cells():
    at(f, p) == 1 => at(szf, p) >= 2
