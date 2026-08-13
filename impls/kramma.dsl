# kramma — 快刀乱麻
# 每条分割线横平竖直且两端在盘面边界上（贯通切割）。
# 每个区域至少一个圆圈，同一区域的圆圈同色。

import "regions"

for p in cells():
    num_eq_cells_with_clue(c, o, p) >= 1

for p in clue_cells(o):
    for q in clue_cells(o):
        at(c, p) == at(c, q) => at(o, p) == at(o, q)

# 同一列缝要么整列都是区界，要么整列都不是。
for p in cells():
    let right = shift(p, 0, 1)
    if right.size == 1:
        for q in cells():
            if col_of(q) == col_of(p):
                let qr = shift(q, 0, 1)
                if qr.size == 1:
                    (at(c, p) != at(c, right)) == (at(c, q) != at(c, qr))
    let down = shift(p, 1, 0)
    if down.size == 1:
        for q in cells():
            if row_of(q) == row_of(p):
                let qd = shift(q, 1, 0)
                if qd.size == 1:
                    (at(c, p) != at(c, down)) == (at(c, q) != at(c, qd))
