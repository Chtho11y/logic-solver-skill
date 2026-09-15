# yajilin — 仙人指路
# 回路经过所有未涂黑的空格；涂黑格不相邻；
# 带箭头的数字表示从此格开始在这个方向中的黑格数（提示格本身不涂黑也不在回路上）。

import "loops"
import "core"

cloop(e)
no_adjacent(x, 1)

for p in cells():
    if has_value(n, p):
        x[p] == 0
        off_loop(e, p)
        num_eq(x[dir(p, d[p])], 1) == n[p]
    else:
        on_loop(e, p) == (x[p] == 0)
