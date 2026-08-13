# bdblock — 边界区块
# 每个区域恰有一种数字；相同数字同区、不同数字异区。
# 黑点顶点恰好伸出三条区界；所有这样的顶点都已给出。

import "regions"

for p in cells():
    num_eq_cells_with_clue(c, n, p) >= 1

for p in clue_cells(n):
    for q in clue_cells(n):
        if at(n, p) == at(n, q):
            at(c, p) == at(c, q)
        if at(n, p) != at(n, q):
            at(c, p) != at(c, q)

for v in corners():
    let deg = num_eq(c.border[edge_of(v)], 1)
    if has_value(o, v):
        deg == 3
    else:
        deg != 3
