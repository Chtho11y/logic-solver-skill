# kurarin — 黑暗回路
# 留白格构成一条不自交回路（每格恰 2 个留白邻居且连通）。
# 格点上的点：1=留白更多 2=涂黑更多 3=一样多（接触的至多四格）。

import "shading"

connected(x, 0)
cc_count(x, 0) == 1
for p in cells():
    is_white(x, p) => n_adj4(x, p, 0) == 2

for v in clue_cells(c):
    let nb = num_eq(x[cell_of(v)], 1)
    let nw = cell_of(v).size - nb
    if at(c, v) == 1:
        nw > nb
    elif at(c, v) == 2:
        nb > nw
    else:
        nb == nw
