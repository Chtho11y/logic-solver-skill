# starbattle — 星战
# 每行、每列、每个区域内的星数等于给定值；任意两颗星不能放在互相接触的格子内。

import "core"

let k = param("stars")

for r in rows:
    num_eq(x[r], 1) == k
for c in cols:
    num_eq(x[c], 1) == k
for reg in regions:
    num_eq(x[reg], 1) == k

for p in cells():
    at(x, p) == 1 => n_adj8(x, p, 1) == 0
