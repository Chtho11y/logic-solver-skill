# lapaz — 拉巴斯
# 涂黑格互不相邻；数字格不涂黑；留白分成 1×2。
# 横向骨牌上的数字 = 该行黑格数；竖向骨牌上的数字 = 该列黑格数。

import "shading"
import "regions"

no_adjacent(x, 1)
clue_cells_white(x, n)

for p in cells():
    is_black(x, p) => at(c.size, p) == 1
    is_white(x, p) => at(c.size, p) == 2

for p in clue_cells(n):
    let horiz = same_reg_dir(c, p, LEFT) or same_reg_dir(c, p, RIGHT)
    let vert = same_reg_dir(c, p, UP) or same_reg_dir(c, p, DOWN)
    horiz => num_eq(x[row(row_of(p))], 1) == at(n, p)
    vert => num_eq(x[col(col_of(p))], 1) == at(n, p)
