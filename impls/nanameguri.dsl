# nanameguri
# 回路经过每个区域恰好一次。必须经过所有含对角线的格子，且不能穿过对角线。
# g: 1=主对角线(NW–SE) 2=副对角线(NE–SW)

import "loops"
import "regions"

cloop(e)

for reg in regions:
    region_crossings(e, reg) == 2

for p in clue_cells(g):
    on_loop(e, p)
    if at(g, p) == 1:
        (link_up(e, p) == 1 and link_right(e, p) == 1) or (link_left(e, p) == 1 and link_down(e, p) == 1)
    if at(g, p) == 2:
        (link_up(e, p) == 1 and link_left(e, p) == 1) or (link_right(e, p) == 1 and link_down(e, p) == 1)
