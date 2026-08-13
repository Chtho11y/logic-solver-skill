# kuroclone — 黑块克隆
# 每个区域内恰好两组连通涂黑格。数字格不能涂黑。涂黑格不能隔区域边界相邻。
# 带箭头的数字 = 其指向的相邻格所在涂黑连通组的面积。
# 未编码：同一区域内的两组须全等。

import "shading"
import "regions"

two_black_groups_per_region(x)
clue_cells_white(x, n)

let sz = cc_size(x)
for p in clue_cells(n):
    if has_value(d, p):
        let nxt = step(p, at(d, p))
        if nxt.size == 1:
            eq(x, nxt, 1)
            at(sz, nxt) == at(n, p)
