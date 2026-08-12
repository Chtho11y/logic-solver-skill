# putteria — 面积填写
# 每个区域中的一格填上等于该区域面积的数字；填数格不能有公共边；
# 每行每列不能有重复数字（0 表示空格）。

import "core"

for reg in regions:
    num_eq(x[reg], reg.size) == 1
    for p in reg:
        at(x, p) == 0 or at(x, p) == reg.size

for p in cells():
    for q in adj4(p):
        not (at(x, p) > 0 and at(x, q) > 0)

for r in rows:
    line_unique(x, r)
for c in cols:
    line_unique(x, c)

def line_unique(x, line):
    for p in line:
        for q in line:
            if before(p, q):
                not (at(x, p) > 0 and at(x, p) == at(x, q))
