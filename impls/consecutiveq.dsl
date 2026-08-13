# consecutiveq — 连续四数组
# 拉丁方。白点=周围四数恰一对连续，黑点=至少两对。未给出的点不约束。

import "fill2"

latin_n(x, board_n())

for v in clue_cells(o):
    let around = cell_of(v)
    if around.size == 4:
        let n = 0
        for p in around:
            for q in around:
                if before(p, q):
                    let n = n + b2i(abs(at(x, p) - at(x, q)) == 1)
        if at(o, v) == 1:
            n == 1
        if at(o, v) == 2:
            n >= 2
