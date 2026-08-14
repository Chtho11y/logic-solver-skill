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
    return any_where(adj4(p), fn (q) -> same_region(p, q) and at(x, q) == at(x, p) + 1)
