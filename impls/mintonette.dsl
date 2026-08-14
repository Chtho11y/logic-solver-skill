# mintonette — 排球/数弯
# 圆圈两两配对，路径覆盖每一格且不交叉。数字 = 该路径转弯次数。

import "paths2"

no_outer_links(e)
linked_same_x(e, x)

for p in cells():
    if has_value(o, p):
        at(x, p) != 0
        cdeg(e, p) == 1
    else:
        at(x, p) != 0
        cdeg(e, p) == 2

for p in clue_cells(o):
    cc_count(x, at(x, p)) == 1
    count_where(clue_cells(o), fn (q) -> not (row_of(p) == row_of(q) and col_of(p) == col_of(q)) and at(x, p) == at(x, q)) == 1

for p in clue_cells(n):
    count_where(cells(), fn (q) -> at(x, q) == at(x, p) and turns(e, q)) == at(n, p)
