# kurodoko — 田鼠挖洞
# 涂黑格互不相邻、留白连通；数字必须在留白格里，表示此格横竖能直接看到的留白格
# 个数（含自身）。

import "shading"

island_rule(x)

for p in clue_cells(n):
    is_white(x, p)
    see4(x, p, 0) + 1 == at(n, p)
