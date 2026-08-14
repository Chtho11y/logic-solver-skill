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
    return any_where(adj4(p), fn (q) -> at(x, q) == at(x, p) + 1)

def is_entry_cell(x, q):
    return at(x, q) == 1 or any_where(adj4(q), fn (r) -> at(x, r) == at(x, q) - 1 and not same_region(q, r))

def entry_index(x, p):
    return count_where(region_of(p), fn (q) -> is_entry_cell(x, q) and at(x, q) <= at(x, p))
