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
    let mates = 0
    for q in clue_cells(o):
        if not (row_of(p) == row_of(q) and col_of(p) == col_of(q)):
            let mates = mates + b2i(at(x, p) == at(x, q))
    mates == 1

for p in clue_cells(n):
    let tcount = 0
    for q in cells():
        let tcount = tcount + b2i(at(x, q) == at(x, p) and turns(e, q))
    tcount == at(n, p)
