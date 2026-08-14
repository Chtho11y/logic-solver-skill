# roma — 罗马
# 每格箭头；每个区域内箭头互不相同。沿箭头移动必达黑圈。

import "fill2"

arrows_never_leave_board(a)

for p in cells():
    at(a, p) <= 3

for reg in regions:
    distinct(a[reg])

for p in cells():
    if has_value(o, p):
        if at(o, p) == 2:
            at(dist, p) == 0
        else:
            at(dist, p) >= 1
    else:
        at(dist, p) >= 1
    for d in [UP, DOWN, LEFT, RIGHT]:
        if not in_grid(p, dr_of(d), dc_of(d)):
            at(a, p) != d
        else:
            let q = step(p, d)
            if has_value(o, p):
                if at(o, p) == 2:
                    true
                else:
                    at(a, p) == d => at(dist, q) == at(dist, p) - 1
            else:
                at(a, p) == d => at(dist, q) == at(dist, p) - 1
