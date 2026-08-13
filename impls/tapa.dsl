# 涂黑格连通、无全黑 2x2；
# 格内一个或多个数字表示与此格接触的（至多）八格中所有连续涂黑段的长度（无序）。
import "shading"

wall_rule(x)
clue_cells_white(x, n)

for p in clue_cells(n):
    tapa_clue(x, n, n2, n3, n4, p)
