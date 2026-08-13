# nothing — 满或空
# 每个区域要么整区在回路上且只进出一次，要么整区不经过。
# 两个未经过的区域不能相邻。

import "loops"
import "regions"

cloop(e)

for reg in regions:
    let vis = region_visited_cells(e, reg)
    vis == 0 or vis == reg.size
    vis == 0 => region_crossings(e, reg) == 0
    vis == reg.size => region_crossings(e, reg) == 2

for p in cells():
    for q in adj4(p):
        if not same_region(p, q):
            on_loop(e, p) or on_loop(e, q)
