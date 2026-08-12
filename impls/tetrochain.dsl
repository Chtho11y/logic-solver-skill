# 每个涂黑连通组均为四格骨牌；所有骨牌对角连通；数字格不能涂黑；
# 数字表示相应方向上的黑格个数。
import "shading"

groups_of_size(x, 1, 4)
connected8(x, 1)
clue_cells_white(x, n)

for p in clue_cells(n):
    if has_value(d, p):
        num_eq(x[dir(p, at(d, p))], 1) == at(n, p)
