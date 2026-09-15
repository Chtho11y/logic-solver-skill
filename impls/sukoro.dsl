# sukoro — 数殖
# 在一些空格里填 1~4；所有填数格连通；每个数字等于其相邻的填数格数；
# 相邻格里不能填相同数字。

import "core"

for p in cells():
    (f[p] == 1) == (x[p] > 0)

connected(f, 1)

for p in cells():
    f[p] == 1 => x[p] == num_eq(f[adj4(p)], 1)
    for q in adj4(p):
        f[p] == 1 and f[q] == 1 => x[p] != x[q]
