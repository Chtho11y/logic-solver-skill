# country — 周游列国
# 回路恰好经过每个区域一次；任意两个隔着区域边界相邻的格子不能都未被经过；
# 数字表示此区域内回路经过的格数。

import "loops"
import "regions"

cloop(e)

for reg in regions:
    region_crossings(e, reg) == 2

for p in cells():
    for q in adj4(p):
        if not same_region(p, q):
            on_loop(e, p) or on_loop(e, q)

for p in clue_cells(n):
    region_visited_cells(e, region_of(p)) == at(n, p)
