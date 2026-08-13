# wafusuma — 和障
# 相邻区域面积不同。格线上圆圈必须介于两区之间，数字=两区面积之和。

import "regions"

neighbour_sizes_differ(c)

for e in clue_cells(k):
    let sides = cell_of(e)
    sides.size == 2
    for p in sides:
        for q in sides:
            if before(p, q):
                at(c, p) != at(c, q)
                at(c.size, p) + at(c.size, q) == at(k, e)
