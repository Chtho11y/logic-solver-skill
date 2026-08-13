# subomino — 无包含码牌
# 数字=面积。相邻两区都不能把其中一个仅通过平移放入另一个。

import "place2"

region_size_clue(c, n)

for p in cells():
    for q in adj4(p):
        if before(p, q):
            at(c, p) != at(c, q) => not can_fit_in(c, p, q) and not can_fit_in(c, q, p)
