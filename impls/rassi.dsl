# rassi — 绳索缝纫
# 每个区域内一条经过该区所有格子的路径。所有路径端点互不接触（含对角）。

import "paths2"
import "regions"

no_outer_links(e)

for p in cells():
    for q in adj4(p):
        if before(p, q):
            if not same_region(p, q):
                link_between(e, p, q) == 0

for reg in regions:
    if reg.size == 1:
        cdeg(e, reg[0]) == 0
    else:
        let ends = count_where(reg, fn (p) -> cdeg(e, p) == 1)
        let links = 0
        for p in reg:
            cdeg(e, p) == 1 or cdeg(e, p) == 2
            for q in adj4(p):
                if same_region(p, q):
                    if before(p, q):
                        let links = links + link_between(e, p, q)
        ends == 2
        links == reg.size - 1

for p in cells():
    for q in adj8(p):
        if before(p, q):
            is_end(e, p) and is_end(e, q) => false

def is_end(e, p):
    if region_of(p).size == 1:
        return true
    return cdeg(e, p) == 1
