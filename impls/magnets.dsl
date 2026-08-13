# magnets — 磁铁
# 两格区域中放置一对正负号或留空；相邻格不能同号。
# 盘外：left/top = 正号个数，right/bottom = 负号个数。

import "regions"
import "outside"

for reg in regions:
    let np = num_eq(x[reg], 1)
    let nm = num_eq(x[reg], 2)
    (np == 0 and nm == 0) or (np == 1 and nm == 1)

for p in cells():
    for q in adj4(p):
        if before(p, q):
            at(x, p) != 0 and at(x, q) != 0 => at(x, p) != at(x, q)

row_count(x, 1, "left")
row_count(x, 2, "right")
col_count(x, 1, "top")
col_count(x, 2, "bottom")
