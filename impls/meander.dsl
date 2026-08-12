# meander — 蜿蜒
# 每个区域包含一条从 1 到 N 的横竖相连的链（N 为区域格数）；
# 互相接触的格子里的数不能相同。

import "fill"
import "regions"

region_1_to_n(x)
touching_differ(x)

for reg in regions:
    for p in reg:
        at(x, p) < reg.size => has_successor(x, p)

def has_successor(x, p):
    let ok = false
    for q in adj4(p):
        if same_region(p, q):
            let ok = ok or (at(x, q) == at(x, p) + 1)
    return ok
