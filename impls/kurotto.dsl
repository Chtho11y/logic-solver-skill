# kurotto — 凝块
# 涂黑一些空格；数字表示与此格相邻的所有涂黑连通组的总面积（同一组只算一次）。

import "shading"

let ids = cc_id(x)
let sz = cc_size(x)

for p in clue_cells(n):
    is_white(x, p)
    if at(n, p) >= 0:
        adjacent_group_area(x, ids, sz, p) == at(n, p)

def adjacent_group_area(x, ids, sz, p):
    let total = 0
    let seen = []
    for q in adj4(p):
        let fresh = is_black(x, q)
        for r in seen:
            let fresh = fresh and at(ids, q) != at(ids, r)
        let total = total + ite(fresh, at(sz, q), 0)
        let seen = seen.append(q)
    return total
