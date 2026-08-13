# renban — 连番窗口
# 每个区域内数字构成连续序列。被粗边框分隔的相邻两数之差等于该边框长度。

import "fill2"

region_consecutive(x)

for p in cells():
    at(x, p) >= 1
    for q in adj4(p):
        if before(p, q):
            if not same_region(p, q):
                abs(at(x, p) - at(x, q)) == region_border_len(region_id(p), region_id(q))
