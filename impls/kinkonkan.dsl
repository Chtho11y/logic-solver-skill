# kinkonkan — 金刚镜
# 每区域恰一面镜子（对角线）。光束与字母配对、反射次数未编码。

import "regions"

for p in cells():
    at(m, p) == 0 or at(m, p) == 1 or at(m, p) == 2

for reg in regions:
    num_eq(m[reg], 0) == reg.size - 1
    num_eq(m[reg], 1) + num_eq(m[reg], 2) == 1
