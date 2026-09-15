# canal — 峡谷
# 所有涂黑格连通且无全黑 2x2；圆圈里的数字在留白格内，表示此格横竖能直接看到的
# 涂黑格个数（不含此格）。

import "shading"

def canal(x, n):
    wall_rule(x)

    for p in clue_cells(n):
        is_white(x, p)
        see4(x, p, 1) == n[p]

canal(x, n)
