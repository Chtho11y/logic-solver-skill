# makaro — 极大箭头
# 白格按区域填 1..N；相邻不同。黑格箭头指向邻接数字中唯一最大者。

import "fill2"

for p in cells():
    if has_value(b, p):
        at(x, p) == 0
    else:
        at(x, p) >= 1

for reg in regions:
    let whites = []
    for p in reg:
        if not has_value(b, p):
            let whites = whites.append(p)
    if whites.size > 0:
        distinct(x[whites])
        for p in whites:
            at(x, p) >= 1
            at(x, p) <= whites.size

for p in cells():
    for q in adj4(p):
        if not has_value(b, p) and not has_value(b, q):
            at(x, p) != at(x, q)

for p in clue_cells(d):
    let q = step(p, at(d, p))
    if not in_grid(p, dr_of(at(d, p)), dc_of(at(d, p))):
        false
    else:
        for n in adj4(p):
            if not has_value(b, n):
                at(x, n) <= at(x, q)
                if not (row_of(n) == row_of(q) and col_of(n) == col_of(q)):
                    at(x, n) < at(x, q)
