# bhaibahan — 同胞回路
# 经过所有圆圈。正交相邻的两圈：一格直行一格转弯。
# 直行圈的数字 = 该直线段内部直行格数。转弯圈仅编码 n=1。

import "loops2"

cloop(e)

for p in clue_cells(o):
    on_loop(e, p)

for p in clue_cells(o):
    for q in adj4(p):
        if has_value(o, q):
            if before(p, q):
                turns(e, p) != turns(e, q)

for p in clue_cells(n):
    on_loop(e, p)
    goes_straight(e, p) => full_straight_len(e, p) - 2 == at(n, p)
    if at(n, p) == 1:
        for d in [UP, DOWN, LEFT, RIGHT]:
            let q = step(p, d)
            if in_grid(p, dr_of(d), dc_of(d)):
                turns(e, p) and link_dir(e, p, d) == 1 => not turns(e, q)
