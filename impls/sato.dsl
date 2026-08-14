# sato — 回娘家
# 圆圈直线滑动；每区域恰好一个落点。数字 = 移动距离（0 不能动）。

import "paths2"
import "regions"

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
    let tips = count_where(cells(), fn (q) -> at(x, q) == at(x, p) and cdeg(e, q) <= 1)
    let sz = count_where(cells(), fn (q) -> at(x, q) == at(x, p))
    (cdeg(e, p) == 0 and tips == 1) or (cdeg(e, p) == 1 and tips == 2)
    if has_value(n, p):
        sz == at(n, p) + 1

for q in cells():
    at(f, q) == b2i(any_where(clue_cells(o), fn (p) -> ite(row_of(q) == row_of(p) and col_of(q) == col_of(p), cdeg(e, p) == 0, cdeg(e, p) == 1 and at(x, q) == at(x, p) and cdeg(e, q) == 1)))

for_each_region_count(f, 1, 1)
