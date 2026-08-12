# slither — 数回
# 连接相邻圆点画一条不和自身交叉的回路；数字表示此格中回路经过的边数。

import "loops"

loop(e)

for p in clue_cells(n):
    cell_edge_count(e, p) == at(n, p)
