# tawa — 砖墙
# 同一行内不能有连续三个涂黑格。每个不在最后一行的涂黑格正下方必须还有涂黑格。
# 数字格不能涂黑。数字表示其周围（斜线计入）除正上方以外的格子中涂黑格的个数。

import "shading"

for w in slide(1, 3):
    num_eq(x[w], 1) < 3

for p in cells():
    if in_grid(p, 1, 0):
        is_black(x, p) => eq(x, shift(p, 1, 0), 1)

clue_cells_white(x, n)

for p in clue_cells(n):
    count_where(adj8(p), fn (q) -> (row_of(q) != row_of(p) - 1 or col_of(q) != col_of(p)) and is_black(x, q)) == at(n, p)
