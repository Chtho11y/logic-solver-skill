# keywest — 群岛之桥
# 圆圈填 0~4；相邻圆圈连线；>0 的圆圈连通成整体。数字 = 度数。相邻圆圈数字不同。

import "paths2"

no_outer_links(e)

for p in cells():
    if has_value(o, p):
        at(x, p) >= 0
        at(x, p) <= 4
        cdeg(e, p) == at(x, p)
    else:
        at(x, p) == 0
        cdeg(e, p) == 0

for p in cells():
    for q in adj4(p):
        if before(p, q):
            if has_value(o, p) and has_value(o, q):
                at(x, p) != at(x, q)
            else:
                link_between(e, p, q) == 0

let npos = 0
for p in clue_cells(o):
    let npos = npos + b2i(at(x, p) > 0)
npos != 0 => connect_links(e)
for p in cells():
    npos == 0 => cdeg(e, p) == 0
