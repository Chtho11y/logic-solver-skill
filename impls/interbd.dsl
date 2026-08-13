# interbd — 国界线
# 每个留白连通组包含且仅包含某一种颜色的全部提示。提示格不能涂黑。
# 数字 = 四邻涂黑格数。每个涂黑格必须至少与两个不同的留白连通组相邻。

import "shading"

clue_cells_white(x, k)

let ids = cc_id(x)
for p in clue_cells(n):
    is_white(x, p)
    n_adj4(x, p, 1) == at(n, p)

# 同色提示同组、异色提示异组（给出颜色与留白组的双射）
for p in clue_cells(k):
    for q in clue_cells(k):
        if before(p, q):
            (at(k, p) == at(k, q)) == (at(ids, p) == at(ids, q))

# 每个留白格都属于某个提示所在的连通组
for p in cells():
    let hit = false
    for q in clue_cells(k):
        let hit = hit or (at(ids, p) == at(ids, q))
    is_white(x, p) => hit

# 每个涂黑格至少邻接两个不同留白组
for p in cells():
    let ngrp = 0
    for q in adj4(p):
        let fresh = is_white(x, q)
        for r in adj4(p):
            if before(r, q):
                let fresh = fresh and not (is_white(x, r) and at(ids, r) == at(ids, q))
        let ngrp = ngrp + b2i(fresh)
    is_black(x, p) => ngrp >= 2
