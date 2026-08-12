# nurimisaki — 数岬
# 留白连通、无全黑或全白 2x2；圆圈标记了所有恰好只和另一个留白格相邻的留白格；
# 圆圈里的数字表示此格横竖能直接看到的留白格数（含自身），0 表示圈内没有数。

import "shading"

white_connected(x)
no_mono_2x2(x)

for p in cells():
    if has_value(n, p):
        is_white(x, p)
        n_adj4(x, p, 0) == 1
    else:
        is_black(x, p) or n_adj4(x, p, 0) != 1

for p in clue_cells(n):
    if at(n, p) > 0:
        see4(x, p, 0) + 1 == at(n, p)
