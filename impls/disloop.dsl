# disloop — 乱序回路
# 提示格不在回路上。单数提示：箭头前方格子所在直线段长度等于该数。
# 多段无序多重集未编码。

import "loops2"

cloop(e)

for p in clue_cells(n):
    off_loop(e, p)
    if has_value(d, p):
        if in_grid(p, dr_of(at(d, p)), dc_of(at(d, p))):
            let q = step(p, at(d, p))
            on_loop(e, q)
            full_straight_len(e, q) == at(n, p)
