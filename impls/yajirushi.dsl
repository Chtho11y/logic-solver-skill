# yajirushi
# 箭头两两对射、中间无箭头且不相邻。所有空格都在某一对箭头之间。

import "fill2"

for p in cells():
    at(a, p) == 8 or at(a, p) <= 3

def h_pair(p, q):
    let mid_arr = count_where(row(row_of(p)), fn (s) -> col_of(p) < col_of(s) and col_of(s) < col_of(q) and at(a, s) != 8)
    let gap = 0
    for s in row(row_of(p)):
        if col_of(p) < col_of(s) and col_of(s) < col_of(q):
            let gap = gap + 1
    return b2i(at(a, p) == RIGHT and at(a, q) == LEFT and mid_arr == 0 and gap >= 1)

def v_pair(p, q):
    let mid_arr = count_where(col(col_of(p)), fn (s) -> row_of(p) < row_of(s) and row_of(s) < row_of(q) and at(a, s) != 8)
    let gap = 0
    for s in col(col_of(p)):
        if row_of(p) < row_of(s) and row_of(s) < row_of(q):
            let gap = gap + 1
    return b2i(at(a, p) == DOWN and at(a, q) == UP and mid_arr == 0 and gap >= 1)

for p in cells():
    let partners = 0
    for q in cells():
        if row_of(p) == row_of(q) and col_of(p) < col_of(q):
            let partners = partners + h_pair(p, q)
        if row_of(p) == row_of(q) and col_of(q) < col_of(p):
            let partners = partners + h_pair(q, p)
        if col_of(p) == col_of(q) and row_of(p) < row_of(q):
            let partners = partners + v_pair(p, q)
        if col_of(p) == col_of(q) and row_of(q) < row_of(p):
            let partners = partners + v_pair(q, p)
    at(a, p) != 8 => partners == 1
    at(a, p) == 8 => partners == 0

for s in cells():
    let cov = 0
    for p in cells():
        for q in cells():
            if row_of(p) == row_of(s) and row_of(q) == row_of(s):
                if col_of(p) < col_of(s) and col_of(s) < col_of(q):
                    let cov = cov + h_pair(p, q)
            if col_of(p) == col_of(s) and col_of(q) == col_of(s):
                if row_of(p) < row_of(s) and row_of(s) < row_of(q):
                    let cov = cov + v_pair(p, q)
    at(a, s) == 8 => cov >= 1
