# haisu — 入数
# 从 S 到 G 的哈密顿路径。数字 N = 此格是第 N 次进入所属区域时被经过。

import "paths2"
import "regions"

no_outer_links(e)

let nmax = rows.size * cols.size
for p in cells():
    at(x, p) >= 1
    at(x, p) <= nmax
distinct(x)

for p in clue_cells(m):
    if at(m, p) == 1:
        at(x, p) == 1
    else:
        at(x, p) == nmax

for p in cells():
    for q in adj4(p):
        if before(p, q):
            (link_between(e, p, q) == 1) == (abs(at(x, p) - at(x, q)) == 1)

for p in cells():
    at(x, p) < nmax => has_next(x, p)
    cdeg(e, p) == 1 or cdeg(e, p) == 2
    at(x, p) == 1 or at(x, p) == nmax => cdeg(e, p) == 1
    at(x, p) > 1 and at(x, p) < nmax => cdeg(e, p) == 2

for p in clue_cells(n):
    entry_index(x, p) == at(n, p)

def has_next(x, p):
    let ok = false
    for q in adj4(p):
        let ok = ok or (at(x, q) == at(x, p) + 1)
    return ok

def entry_index(x, p):
    let total = 0
    for q in region_of(p):
        let is_entry = at(x, q) == 1
        for r in adj4(q):
            let is_entry = is_entry or (at(x, r) == at(x, q) - 1 and not same_region(q, r))
        let total = total + b2i(is_entry and at(x, q) <= at(x, p))
    return total
