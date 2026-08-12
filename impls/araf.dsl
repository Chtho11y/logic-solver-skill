# araf — 炼狱
# 每个区域恰好包含两个有数字的圆圈，区域面积严格介于这两个数字之间。

import "regions"

for p in cells():
    num_eq_cells_with_clue(c, n, p) == 2

for p in clue_cells(n):
    for q in clue_cells(n):
        if before(p, q):
            if at(n, p) < at(n, q):
                at(c, p) == at(c, q) => at(c.size, p) > at(n, p) and at(c.size, p) < at(n, q)
            if at(n, p) > at(n, q):
                at(c, p) == at(c, q) => at(c.size, p) > at(n, q) and at(c.size, p) < at(n, p)
            if at(n, p) == at(n, q):
                at(c, p) != at(c, q)
