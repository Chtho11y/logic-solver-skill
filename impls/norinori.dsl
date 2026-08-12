# norinori — 海苔
# 在每个区域内涂黑恰好两格，使得每一组涂黑的连通组恰好有两格。

import "shading"

for reg in regions:
    num_eq(x[reg], 1) == 2

let s = cc_size(x)
for p in cells():
    is_black(x, p) => at(s, p) == 2
