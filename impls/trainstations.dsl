# trainstations — 铁轨
# 经过所有格子。仅在数字格允许自交；数字格不转弯。
# 按 1..k 顺序经过未编码。

import "loops2"

full_cross_loop(e)

for p in cells():
    if has_value(n, p):
        let d = cdeg(e, p)
        d == 2 or d == 4
        d == 2 => goes_straight(e, p)
    else:
        cdeg(e, p) == 2
