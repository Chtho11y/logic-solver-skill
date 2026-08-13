# batten — 双色蛋糕
# 盘面外的数字表示此行或此列内涂黑格的个数。
# 所有呈黑白相间棋盘格图案的 2×2 区域都已被标记（标记与棋盘格 2×2 一一对应）。

import "shading"
import "outside"

col_count(x, 1, "top")
row_count(x, 1, "left")

for p in cells():
    let right = shift(p, 0, 1)
    let down = shift(p, 1, 0)
    let diag = shift(p, 1, 1)
    if right.size + down.size + diag.size == 3:
        let w = cell_of(p) and right and down and diag
        let checker = (num_eq(x[w], 1) == 2) and (at(x, p) == at(x, diag))
        has_value(m, p) => checker
        checker => has_value(m, p)
