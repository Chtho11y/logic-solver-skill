# 涂黑格互不相邻、留白连通；
# 留白格内带箭头的数字 = 从此格开始该方向的涂黑格数；
# 这些提示数若位于涂黑格内则不提供任何信息。
import "shading"

island_rule(x)

for p in clue_cells(n):
    if has_value(d, p):
        is_white(x, p) => num_eq(x[dir(p, at(d, p))], 1) == at(n, p)
