# japanesesums — 日本和
# 给定数字每行每列至多一次。盘外依次为各填数段之和。

import "fill2"

let vals = values_param([1, 2])

for p in cells():
    allowed_or_empty(x, p, vals)

each_at_most_once(x, vals)

for i in rows:
    apply_run_sums(x, i, side_clue("left", row_of(i[0])))

for j in cols:
    apply_run_sums(x, j, side_clue("top", col_of(j[0])))
