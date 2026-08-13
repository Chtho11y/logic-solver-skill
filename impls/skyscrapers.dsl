# skyscrapers — 摩天楼
# 拉丁方 1..N。盘外数字=该方向能看到的楼数（高楼遮挡矮楼）。

import "fill2"

if has_param("values"):
    let vals = param("values")
    for p in cells():
        allowed_or_empty(x, p, vals)
    each_once(x, vals)
else:
    latin_n(x, board_n())

for i in rows:
    let k = side_clue("left", row_of(i[0]))
    if not no_clue(k):
        vis_count(x, i) == k
    let kr = side_clue("right", row_of(i[0]))
    if not no_clue(kr):
        vis_count_row_rev(x, i) == kr

for j in cols:
    let k = side_clue("top", col_of(j[0]))
    if not no_clue(k):
        vis_count(x, j) == k
    let kb = side_clue("bottom", col_of(j[0]))
    if not no_clue(kb):
        vis_count_col_rev(x, j) == kb
