# evolmino — 生长方块
# 每一组连通的正方形（涂黑）都恰有一个格子落在某条箭头上。
# 每条箭头至少穿过两组。沿箭头方向后一组比前一组多一格。
# 未编码：后一组须为前一组的平移（不可旋转翻转）再多一格。
# a>0 标记箭头经过的格子（同号 = 同一条箭头）；d 写在每个箭头格上。

import "shading"

clue_cells_black(x, a)
cc_count(x, 1) == clue_cells(a).size

let sz = cc_size(x)
for p in clue_cells(a):
    let n = 0
    for q in clue_cells(a):
        let n = n + b2i(at(a, p) == at(a, q))
    n >= 2

for p in clue_cells(a):
    if has_value(d, p):
        let found = false
        for s in dir(p, at(d, p)):
            if has_value(a, s):
                if at(a, s) == at(a, p) and not found:
                    at(sz, s) == at(sz, p) + 1
                    let found = true
