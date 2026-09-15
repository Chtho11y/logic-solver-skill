# araf — 炼狱
# 每个区域恰好包含两个有数字的圆圈，区域面积严格介于这两个数字之间。

import "regions"

for p in cells():
    num_eq_cells_with_clue(c, n, p) == 2

for p in clue_cells(n):
    for q in clue_cells(n):
        if before(p, q):
            if n[p] < n[q]:
                c[p] == c[q] => c.size[p] > n[p] and c.size[p] < n[q]
            if n[p] > n[q]:
                c[p] == c[q] => c.size[p] > n[q] and c.size[p] < n[p]
            if n[p] == n[q]:
                c[p] != c[q]
