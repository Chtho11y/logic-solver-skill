# tents — 帐篷
# 每棵树配一顶相邻的帐篷（一一对应）；任意两顶帐篷不能接触；
# 盘面外的数字表示此行或此列内帐篷的个数。
# a 记录帐篷指向的树: 0 无, 1 上, 2 下, 3 左, 4 右。

import "core"
import "outside"

for p in clue_cells(t):
    at(x, p) == 0

for p in cells():
    (at(a, p) > 0) == (at(x, p) == 1)
    for code, dr, dc in [[1, -1, 0], [2, 1, 0], [3, 0, -1], [4, 0, 1]]:
        let q = step_rc(p, dr, dc)
        if q.size == 0:
            at(a, p) != code
        else:
            if not has_value(t, q):
                at(a, p) != code

# 每棵树恰好被一顶帐篷选中。
for p in clue_cells(t):
    tree_tents(a, p) == 1

for p in cells():
    at(x, p) == 1 => n_adj8(x, p, 1) == 0

row_count(x, 1, "left")
col_count(x, 1, "top")

def step_rc(p, dr, dc):
    return shift(p, dr, dc)

def tree_tents(a, p):
    let total = 0
    for code, dr, dc in [[2, -1, 0], [1, 1, 0], [4, 0, -1], [3, 0, 1]]:
        let q = shift(p, dr, dc)
        if q.size == 1:
            let total = total + b2i(at(a, q) == code)
    return total
