# cojun — 叠叠高
# 区域 1..N；相邻不同。同区域内纵向相邻则上格大于下格。

import "fill2"

region_1_to_n(x)
adjacent_differ(x)

for p in cells():
    let q = shift(p, 1, 0)
    if in_grid(p, 1, 0):
        if same_region(p, q):
            at(x, p) > at(x, q)
