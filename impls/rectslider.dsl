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
    let tips = count_where(cells(), fn (q) -> at(x, q) == at(x, p) and cdeg(e, q) <= 1)
    let sz = count_where(cells(), fn (q) -> at(x, q) == at(x, p))
    (cdeg(e, p) == 0 and tips == 1) or (cdeg(e, p) == 1 and tips == 2)
    if has_value(n, p):
        sz == at(n, p) + 1

for q in cells():
    at(f, q) == b2i(any_where(clue_cells(b), fn (p) -> ite(row_of(q) == row_of(p) and col_of(q) == col_of(p), cdeg(e, p) == 0, cdeg(e, p) == 1 and at(x, q) == at(x, p) and cdeg(e, q) == 1)))

is_rect_group(f, 1)
let szf = cc_size(f)
for p in cells():
    at(f, p) == 1 => at(szf, p) >= 2
