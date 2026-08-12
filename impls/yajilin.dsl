# yajilin — 仙人指路
# 回路经过所有未涂黑的空格；涂黑格不相邻；
# 带箭头的数字表示从此格开始在这个方向中的黑格数（提示格本身不涂黑也不在回路上）。

import "loops"
import "core"

loop_visits_all_but(e, x)
no_adjacent(x, 1)

for p in clue_cells(n):
    at(x, p) == 0
    off_loop(e, p)
    num_eq(x[dir(p, at(d, p))], 1) == at(n, p)
