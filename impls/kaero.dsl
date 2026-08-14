# kaero — 归路
# 字母沿正交路径移动；每区域最终恰好一种字母，同字母同区。路径不交叉。

import "paths2"
import "regions"

no_outer_links(e)
linked_same_x(e, x)

for p in cells():
    if has_value(n, p):
        at(x, p) == cell_idx(p) + 1
        cdeg(e, p) == 0 or cdeg(e, p) == 1
    else:
        (at(x, p) == 0 and cdeg(e, p) == 0) or (at(x, p) != 0 and (cdeg(e, p) == 1 or cdeg(e, p) == 2))

for p in clue_cells(n):
    cc_count(x, at(x, p)) == 1
    let tips = count_where(cells(), fn (q) -> at(x, q) == at(x, p) and cdeg(e, q) <= 1)
    (cdeg(e, p) == 0 and tips == 1) or (cdeg(e, p) == 1 and tips == 2)

for q in cells():
    let ty = sum_where(clue_cells(n), fn (p) -> ite(row_of(q) == row_of(p) and col_of(q) == col_of(p), cdeg(e, p) == 0, cdeg(e, p) == 1 and at(x, q) == at(x, p) and cdeg(e, q) == 1), fn (p) -> at(n, p))
    at(f, q) == ty

for p in cells():
    for q in cells():
        if before(p, q):
            if same_region(p, q):
                at(f, p) != 0 and at(f, q) != 0 => at(f, p) == at(f, q)
            else:
                at(f, p) != 0 and at(f, q) != 0 => at(f, p) != at(f, q)

for reg in regions:
    let any = count_where(reg, fn (p) -> at(f, p) != 0)
    any >= 1
