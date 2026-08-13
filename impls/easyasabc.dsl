# easyasabc — 简单字符
# 给定字母每行每列各一次。盘外字符=从该方向看到的第一个字母。

import "fill2"

let vals = values_param([1, 2])

for p in cells():
    allowed_or_empty(x, p, vals)

each_once(x, vals)

for i in rows:
    let k = side_clue("left", row_of(i[0]))
    if not no_clue(k):
        first_nonzero(x, i) == k
    let kr = side_clue("right", row_of(i[0]))
    if not no_clue(kr):
        first_nonzero_row_rev(x, i) == kr

for j in cols:
    let k = side_clue("top", col_of(j[0]))
    if not no_clue(k):
        first_nonzero(x, j) == k
    let kb = side_clue("bottom", col_of(j[0]))
    if not no_clue(kb):
        first_nonzero_col_rev(x, j) == kb
