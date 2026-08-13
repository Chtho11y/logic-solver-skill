# martini — 马提尼
# 每个区域内至多一组连通涂黑格；不同区域的涂黑组不相邻。
# 所有涂黑格对角连通。黑圈必须涂黑，白圈必须留白。
# 白圈里的数字 = 其所在留白连通组中的白圈个数（含自身）。

import "shading"
import "regions"

at_most_one_black_group_per_region(x)
connected8(x, 1)

for p in clue_cells(o):
    if at(o, p) == 2:
        is_black(x, p)
    if at(o, p) == 1:
        is_white(x, p)

let ids = cc_id(x)
for p in clue_cells(n):
    is_white(x, p)
    let total = 0
    for q in clue_cells(o):
        if at(o, q) == 1:
            let total = total + b2i(at(ids, p) == at(ids, q))
    total == at(n, p)
