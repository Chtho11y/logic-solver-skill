# tateyoko — 翠竹交错
# 白格画横或竖。白数字=线段长；黑数字=引出线段数。一线段至多一个白数字。

import "fill2"

for p in cells():
    if has_value(b, p):
        at(x, p) == 0
    else:
        at(x, p) >= 1
        at(x, p) <= 2

def run_len(p, axis):
    # Prefix machine along both ends of a row (axis 0, value 1) or column (axis 1, value 2).
    let v = ite(axis == 0, 1, 2)
    let n = 1
    let alive = true
    for q in line_from(p, ite(axis == 0, LEFT, UP)):
        let n = n + b2i(alive and at(x, q) == v)
        let alive = alive and at(x, q) == v
    let alive2 = true
    for q in line_from(p, ite(axis == 0, RIGHT, DOWN)):
        let n = n + b2i(alive2 and at(x, q) == v)
        let alive2 = alive2 and at(x, q) == v
    return n

for p in clue_cells(n):
    if has_value(b, p):
        let k = 0
        for d in dirs4:
            let k = k + b2i(nb(x, p, d) == ite(is_horizontal(d), 1, 2))
        k == at(n, p)
    else:
        at(x, p) == 1 => run_len(p, 0) == at(n, p)
        at(x, p) == 2 => run_len(p, 1) == at(n, p)

for p in clue_cells(n):
    for q in clue_cells(n):
        if before(p, q):
            if not has_value(b, p) and not has_value(b, q):
                if row_of(p) == row_of(q):
                    let allh = b2i(at(x, p) == 1 and at(x, q) == 1)
                    for s in row(row_of(p)):
                        if col_of(p) < col_of(s) and col_of(s) < col_of(q):
                            let allh = allh * b2i(at(x, s) == 1)
                        if col_of(q) < col_of(s) and col_of(s) < col_of(p):
                            let allh = allh * b2i(at(x, s) == 1)
                    allh == 0
                if col_of(p) == col_of(q):
                    let allv = b2i(at(x, p) == 2 and at(x, q) == 2)
                    for s in col(col_of(p)):
                        if row_of(p) < row_of(s) and row_of(s) < row_of(q):
                            let allv = allv * b2i(at(x, s) == 2)
                        if row_of(q) < row_of(s) and row_of(s) < row_of(p):
                            let allv = allv * b2i(at(x, s) == 2)
                    allv == 0
