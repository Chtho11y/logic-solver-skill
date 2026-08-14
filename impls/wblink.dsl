# wblink — 黑白配
# 黑圈与白圈两两配对，路径横平竖直可转弯，互不交叉（端点也不交）。

import "paths2"

no_outer_links(e)
linked_same_x(e, x)

for p in cells():
    if has_value(o, p):
        at(x, p) != 0
        cdeg(e, p) == 1
    else:
        (at(x, p) == 0 and cdeg(e, p) == 0) or (at(x, p) != 0 and cdeg(e, p) == 2)

for p in clue_cells(o):
    cc_count(x, at(x, p)) == 1
    count_where(clue_cells(o), fn (q) -> not (row_of(p) == row_of(q) and col_of(p) == col_of(q)) and at(x, p) == at(x, q) and at(o, p) == at(o, q)) == 0
    count_where(clue_cells(o), fn (q) -> not (row_of(p) == row_of(q) and col_of(p) == col_of(q)) and at(x, p) == at(x, q) and at(o, p) != at(o, q)) == 1
