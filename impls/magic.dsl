# magic — 魔夏
# 数码每行每列各一次。盘外=连续数码组成的多位数之和。叉格不填。

import "fill2"

let vals = values_param([1, 2])

for p in cells():
    if has_value(m, p):
        at(x, p) == 0
    else:
        allowed_or_empty(x, p, vals)

each_once(x, vals)

for i in rows:
    let k = side_clue("left", row_of(i[0]))
    if not no_clue(k):
        magic_line_value(x, i) == k

for j in cols:
    let k = side_clue("top", col_of(j[0]))
    if not no_clue(k):
        magic_line_value(x, j) == k
