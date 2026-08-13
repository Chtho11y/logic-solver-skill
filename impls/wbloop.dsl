# wbloop — 黑白回路
# 经过所有圆圈。同一直线段上的圆圈必须同色（异色需要中间有转弯）。
# 沿回路隔格的连续圆圈转弯次数未完全编码。

import "loops2"

cloop(e)

for p in clue_cells(o):
    on_loop(e, p)

for p in clue_cells(o):
    for q in clue_cells(o):
        if before(p, q):
            if row_of(p) == row_of(q):
                let cover = true
                let r = row_of(p)
                let c1 = col_of(p)
                let c2 = col_of(q)
                for s in cells():
                    if row_of(s) == r and col_of(s) > c1 and col_of(s) < c2:
                        let cover = cover and on_loop(e, s) and goes_horizontal(e, s)
                    if row_of(s) == r and col_of(s) >= c1 and col_of(s) < c2:
                        let cover = cover and (link_right(e, s) == 1)
                cover => at(o, p) == at(o, q)
            if col_of(p) == col_of(q):
                let cover = true
                let c = col_of(p)
                let r1 = row_of(p)
                let r2 = row_of(q)
                for s in cells():
                    if col_of(s) == c and row_of(s) > r1 and row_of(s) < r2:
                        let cover = cover and on_loop(e, s) and goes_vertical(e, s)
                    if col_of(s) == c and row_of(s) >= r1 and row_of(s) < r2:
                        let cover = cover and (link_down(e, s) == 1)
                cover => at(o, p) == at(o, q)
