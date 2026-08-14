# cbanana — 巧克力香蕉
# 每个涂黑的连通组都是长方形，每个留白的连通组都不是长方形；
# 数字表示其所在连通组的面积。

import "shading"

is_rect_group(x, 1)

let ids = cc_id(x)
let sz = cc_size(x)

for p in clue_cells(n):
    at(sz, p) == at(n, p)

# 每个白连通组必须“不是长方形”：存在一个 2x2 窗口恰好含它的 3 个格子。
for p in cells():
    is_white(x, p) => any_where(slide(2, 2), fn (w) -> num_eq(x[w], 0) == 3 and all_where(w, fn (q) -> is_black(x, q) or at(ids, q) == at(ids, p)))
