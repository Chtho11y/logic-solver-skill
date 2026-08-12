# cave — 山洞
# 涂黑格都能沿涂黑格连通到盘面边界；留白格连通成一个整体；
# 数字在留白格里，表示此格横竖能直接看到的留白格数（含自身）。

import "shading"

white_connected(x)
group_touches_border(x, 1)

for p in clue_cells(n):
    is_white(x, p)
    see4(x, p, 0) + 1 == at(n, p)
