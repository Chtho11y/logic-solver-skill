# yinyang — 阴阳
# 黑白圆圈分别横竖连通为一个整体，且均不形成 2x2 的区域。

import "shading"

def yinyang(x, g):
    for p in clue_cells(g):
        x[p] == g[p]

    black_connected(x)
    white_connected(x)
    no_mono_2x2(x)

yinyang(x, g)
