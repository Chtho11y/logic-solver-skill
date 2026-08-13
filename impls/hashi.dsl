# hashi — 数桥
# 岛与岛之间 1 或 2 座直桥，互不交叉、不穿过岛；数字 = 连出桥数；全部岛连通。

import "paths2"

no_outer_links(e)
no_outer_links(t)

for ed in edges():
    at(t, ed) <= at(e, ed)

let ni = clue_cells(n).size
if ni >= 2:
    connect_links(e)


for p in cells():
    if has_value(n, p):
        cdeg(e, p) + cdeg(t, p) == at(n, p)
    else:
        cdeg(e, p) == 0 or cdeg(e, p) == 2
        cdeg(e, p) == 2 => goes_straight(e, p)
        goes_horizontal(e, p) => at(t, left_edge(p)) == at(t, right_edge(p))
        goes_vertical(e, p) => at(t, up_edge(p)) == at(t, down_edge(p))
