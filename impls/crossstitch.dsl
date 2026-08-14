# crossstitch — 十字绣
# 每格 0=空 1=\ 2=/ 3=交叉。格点度数 0 或 2。交叉格不能正交相邻。
# 圆圈数字 = 四角中被经过的个数。箭头数字 = 该方向交叉格数（直到黑格或边界）。
# 恰好两条回路的全局计数未编码。

import "loops2"

def stroke_at_corner(x, p, v):
    let backslash = (row_of(v) == row_of(p) and col_of(v) == col_of(p)) or (row_of(v) == row_of(p) + 1 and col_of(v) == col_of(p) + 1)
    let slash = (row_of(v) == row_of(p) and col_of(v) == col_of(p) + 1) or (row_of(v) == row_of(p) + 1 and col_of(v) == col_of(p))
    return (backslash and (at(x, p) == 1 or at(x, p) == 3)) or (slash and (at(x, p) == 2 or at(x, p) == 3))

def corner_degree(x, v):
    return count_where(cell_of(v), fn (p) -> stroke_at_corner(x, p, v))

for p in cells():
    if marked(w, p):
        at(x, p) == 0

for v in corners():
    let d = corner_degree(x, v)
    d == 0 or d == 2

for p in cells():
    for q in adj4(p):
        if before(p, q):
            at(x, p) == 3 and at(x, q) == 3 => false

for p in clue_cells(n):
    if has_value(d, p):
        let total = 0
        let alive = true
        for q in dir(p, at(d, p)):
            if marked(w, q):
                let alive = false
            let total = total + b2i(alive and at(x, q) == 3)
        total == at(n, p)
    else:
        count_where(corner_of(p), fn (v) -> corner_degree(x, v) == 2) == at(n, p)
