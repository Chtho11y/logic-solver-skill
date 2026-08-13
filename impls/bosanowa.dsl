# bosanowa — 邻差和
# 每个圆圈中的正整数等于它与横竖相邻填数之差的绝对值之和。

import "fill2"

for p in cells():
    if has_value(o, p):
        at(x, p) >= 1
        let s = 0
        for q in adj4(p):
            if has_value(o, q):
                let s = s + abs(at(x, p) - at(x, q))
        at(x, p) == s
    else:
        at(x, p) == 0
