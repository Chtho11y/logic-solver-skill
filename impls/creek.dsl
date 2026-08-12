# creek — 溪流
# 涂黑一些格子使留白格连通；格点上的圆圈数字表示接触此顶点的涂黑格数。

import "shading"

white_connected(x)

for v in clue_cells(n):
    num_eq(x[cell_of(v)], 1) == at(n, v)
