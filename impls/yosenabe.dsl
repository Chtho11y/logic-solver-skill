# yosenabe — 火锅
# 每个圆圈直线滑入灰色锅；每锅至少一个；可越过其他锅。锅内数字 = 落入圆圈数字之和。

import "paths2"
import "regions"

no_outer_links(e)
linked_same_x(e, x)

for p in cells():
    if has_value(o, p):
        at(x, p) == cell_idx(p) + 1
        cdeg(e, p) == 0 or cdeg(e, p) == 1
    else:
        (at(x, p) == 0 and cdeg(e, p) == 0) or (at(x, p) != 0 and (cdeg(e, p) == 1 or cdeg(e, p) == 2))
        cdeg(e, p) == 2 => goes_straight(e, p)

for p in clue_cells(o):
    cc_count(x, at(x, p)) == 1
    let tips = 0
    for q in cells():
        let tips = tips + b2i(at(x, q) == at(x, p) and cdeg(e, q) <= 1)
    (cdeg(e, p) == 0 and tips == 1) or (cdeg(e, p) == 1 and tips == 2)

for q in cells():
    let dest = false
    for p in clue_cells(o):
        let is_dest = false
        if row_of(q) == row_of(p) and col_of(q) == col_of(p):
            let is_dest = cdeg(e, p) == 0
        else:
            let is_dest = cdeg(e, p) == 1 and at(x, q) == at(x, p) and cdeg(e, q) == 1
        let dest = dest or is_dest
    at(f, q) == b2i(dest)
    at(f, q) == 1 => has_value(g, q)

for reg in regions:
    let ng = 0
    for p in reg:
        if has_value(g, p):
            let ng = ng + 1
    if ng > 0:
        num_eq(f[reg], 1) >= 1
        for p in reg:
            if has_value(k, p):
                let sm = 0
                for s in clue_cells(o):
                    let inreg = false
                    for q in reg:
                        let inreg = inreg or (at(f, q) == 1 and at(x, q) == at(x, s))
                    if has_value(n, s):
                        let sm = sm + b2i(inreg) * at(n, s)
                sm == at(k, p)
