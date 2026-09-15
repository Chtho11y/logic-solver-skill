# 回路；不在回路上的格子构成若干连通岛，每岛恰好一个数字，数字 = 岛的格数。
import "loops"
import "core"

def nuriloop(e, x, n):
    cloop(e)
    for p in cells():
        on_loop(e, p) == (x[p] == 0)
    for p in clue_cells(n):
        x[p] == 1
        cc_size(x)[p] == n[p]
    cc_count(x, 1) == clue_cells(n).size

nuriloop(e, x, n)
