# firefly — 萤火虫
# 从每个圆圈黑点方向引出一条格心路径，在某一圆圈的非黑点侧结束。
# 路径不交叉；全部圆圈连通。数字 = 引出路径的转弯次数。

import "paths2"

no_outer_links(e)
connect_links(e)

for p in cells():
    for q in adj4(p):
        if before(p, q):
            if not has_value(o, p) and not has_value(o, q):
                link_between(e, p, q) == 1 => at(x, p) == at(x, q)

for p in cells():
    if has_value(o, p):
        cdeg(e, p) >= 1
        at(x, p) == 0
        link_dir(e, p, at(d, p)) == 1
    else:
        (cdeg(e, p) == 0 and at(x, p) == 0) or (cdeg(e, p) == 2 and at(x, p) != 0)

for p in clue_cells(o):
    let nid = cell_idx(p) + 1
    if not in_grid(p, dr_of(at(d, p)), dc_of(at(d, p))):
        false
    else:
        let q = step(p, at(d, p))
        if has_value(o, q):
            if has_value(n, p):
                at(n, p) == 0
            if in_grid(q, dr_of(at(d, q)), dc_of(at(d, q))):
                let back = step(q, at(d, q))
                if row_of(back) == row_of(p) and col_of(back) == col_of(p):
                    false
        else:
            at(x, q) == nid

for p in clue_cells(n):
    let nid = cell_idx(p) + 1
    if in_grid(p, dr_of(at(d, p)), dc_of(at(d, p))):
        let q = step(p, at(d, p))
        if not has_value(o, q):
            let tcount = count_where(cells(), fn (r) -> at(x, r) == nid and turns(e, r))
            tcount == at(n, p)
