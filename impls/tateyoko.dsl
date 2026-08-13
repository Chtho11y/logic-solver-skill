# tateyoko — 翠竹交错
# 白格画横或竖。白数字=线段长；黑数字=引出线段数。一线段至多一个白数字。

import "fill2"

for p in cells():
    if has_value(b, p):
        at(x, p) == 0
    else:
        at(x, p) >= 1
        at(x, p) <= 2

def hlen(p):
    let n = 1
    let alive = true
    for q in dir(p, LEFT):
        let n = n + b2i(alive and at(x, q) == 1)
        let alive = alive and at(x, q) == 1
    let alive2 = true
    for q in dir(p, RIGHT):
        let n = n + b2i(alive2 and at(x, q) == 1)
        let alive2 = alive2 and at(x, q) == 1
    return n

def vlen(p):
    let n = 1
    let alive = true
    for q in dir(p, UP):
        let n = n + b2i(alive and at(x, q) == 2)
        let alive = alive and at(x, q) == 2
    let alive2 = true
    for q in dir(p, DOWN):
        let n = n + b2i(alive2 and at(x, q) == 2)
        let alive2 = alive2 and at(x, q) == 2
    return n

for p in clue_cells(n):
    if has_value(b, p):
        let k = 0
        let q = step(p, LEFT)
        if q.size > 0:
            let k = k + b2i(at(x, q) == 1)
        let q = step(p, RIGHT)
        if q.size > 0:
            let k = k + b2i(at(x, q) == 1)
        let q = step(p, UP)
        if q.size > 0:
            let k = k + b2i(at(x, q) == 2)
        let q = step(p, DOWN)
        if q.size > 0:
            let k = k + b2i(at(x, q) == 2)
        k == at(n, p)
    else:
        at(x, p) == 1 => hlen(p) == at(n, p)
        at(x, p) == 2 => vlen(p) == at(n, p)

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
