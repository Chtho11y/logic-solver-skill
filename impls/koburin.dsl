# 仙人指路 + 数字格不在回路上、不涂黑，数字 = 正交邻格黑格数。
import "loops"
import "core"

cloop(e)
no_adjacent(x, 1)
for p in cells():
    if has_value(n, p):
        x[p] == 0
        off_loop(e, p)
        n_adj4(x, p, 1) == n[p]
    else:
        on_loop(e, p) == (x[p] == 0)
