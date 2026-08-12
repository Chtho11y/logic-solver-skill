# aquapelago — 千岛湖
# 涂黑格互不相邻、留白连通、无全白 2x2；数字格必须涂黑，
# 数字表示其所在对角连通黑格组的格数（含自身）。

import "shading"

island_rule(x)
no_white_2x2(x)

let s8 = cc8_size(x)
for p in clue_cells(n):
    is_black(x, p)
    at(s8, p) == at(n, p)
