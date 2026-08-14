# forestwalk — 森林行者
# 绿格度数 3，白格 0 或 2；单一网络。数字 = 所在连续白段格数。

import "paths2"

no_outer_links(e)
connect_links(e)

let nmax = rows.size * cols.size

for p in cells():
    if has_value(g, p):
        cdeg(e, p) == 3
        at(u, p) == nmax
        at(z, p) == 0
    else:
        cdeg(e, p) == 0 or cdeg(e, p) == 2
        cdeg(e, p) == 0 => at(u, p) == nmax and at(z, p) == 0
        cdeg(e, p) == 2 => at(u, p) <= cell_idx(p) and ((at(u, p) == cell_idx(p)) == (at(z, p) == 0))

for p in cells():
    for q in adj4(p):
        if before(p, q):
            if not has_value(g, p) and not has_value(g, q):
                link_between(e, p, q) == 1 => at(u, p) == at(u, q)

for p in cells():
    if not has_value(g, p):
        at(z, p) > 0 => any_where(adj4(p), fn (q) -> not has_value(g, q) and link_between(e, p, q) == 1 and at(u, q) == at(u, p) and at(z, q) == at(z, p) - 1)

for p in clue_cells(n):
    cdeg(e, p) == 2
    let sz = count_where(cells(), fn (q) -> at(u, q) == at(u, p))
    sz == at(n, p)
