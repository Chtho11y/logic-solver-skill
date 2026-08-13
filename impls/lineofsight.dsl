# lineofsight — 视线
# 数回（格线回路）。数字+方向：该方向最近一条回路线段的长度；0 = 该方向没有线段。

import "loops2"

loop(e)

for p in clue_cells(n):
    if has_value(d, p):
        nearest_seg_len(e, p, at(d, p)) == at(n, p)
