# fuzuli — 冗余
# 从给定列表填数，每行每列各出现一次；无全填 2×2；叉格不填。

import "fill2"

let vals = values_param([1, 2])

for p in cells():
    if has_value(m, p):
        at(x, p) == 0
    else:
        allowed_or_empty(x, p, vals)

each_once(x, vals)

for w in slide(2, 2):
    num_eq(x[w], 0) >= 1
