# nanro — 物以类聚
# 在一些格子里填数使所有填数格连通，且没有 2x2 全部填数；
# 填入的数等于该区域内填数格的个数；每个区域至少填一个数；
# 不同区域中相邻的格子不能有相同数。

import "core"

for p in cells():
    (at(f, p) == 1) == (at(x, p) > 0)

connected(f, 1)

for w in slide(2, 2):
    num_eq(f[w], 1) < 4

for reg in regions:
    let cnt = num_eq(f[reg], 1)
    cnt >= 1
    for p in reg:
        at(f, p) == 1 => at(x, p) == cnt

for p in cells():
    for q in adj4(p):
        if not same_region(p, q):
            not (at(f, p) == 1 and at(f, q) == 1 and at(x, p) == at(x, q))
