# tentaisho — 星系
# 每个区域恰好一个圆点；区域绕该圆点 180° 旋转对称。
# 圆点写在格子中心（格线/格点上的圆心未建模）。

import "regions"

one_clue_per_region(c, o)

for p in cells():
    for t in clue_cells(o):
        let q = shift(t, row_of(t) - row_of(p), col_of(t) - col_of(p))
        if q.size == 0:
            at(c, p) != at(c, t)
        if q.size == 1:
            at(c, p) == at(c, t) => at(c, q) == at(c, t)
