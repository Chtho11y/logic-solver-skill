# context — 黑斜白邻
# 涂黑格互不相邻、留白连通；留白格内的数字表示相邻涂黑格数，
# 涂黑格内的数字表示对角接触的涂黑格数。

import "shading"

island_rule(x)

for p in clue_cells(n):
    is_white(x, p) => n_adj4(x, p, 1) == at(n, p)
    is_black(x, p) => n_diag4(x, p, 1) == at(n, p)
