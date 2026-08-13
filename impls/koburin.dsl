# koburin — 仙人指邻
# 回路经过所有未涂黑空格；涂黑格不相邻。
# 数字格不涂黑、不在回路上；数字 = 四邻黑格数。

import "loops"

cloop(e)
no_adjacent(x, 1)

for p in cells():
    if has_value(n, p):
        at(x, p) == 0
        off_loop(e, p)
        n_adj4(x, p, 1) == at(n, p)
    else:
        on_loop(e, p) == (at(x, p) == 0)
