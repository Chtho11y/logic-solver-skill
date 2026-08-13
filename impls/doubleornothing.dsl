# doubleornothing — 双或无
# 两条不自交回路。空格恰好被一条经过；加号格要么两条在此交叉，要么都不经过。

import "loops2"

cloop(e)
cloop(f)

for p in cells():
    for q in adj4(p):
        if before(p, q):
            link_between(e, p, q) + link_between(f, p, q) <= 1

for p in cells():
    if marked(g, p):
        let both = on_loop(e, p) and on_loop(f, p)
        let none = off_loop(e, p) and off_loop(f, p)
        both or none
        both => (goes_horizontal(e, p) and goes_vertical(f, p)) or (goes_vertical(e, p) and goes_horizontal(f, p))
    else:
        on_loop(e, p) != on_loop(f, p)
