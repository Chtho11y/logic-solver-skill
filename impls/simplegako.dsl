# 每个数字等于它在所在行和列中出现的次数（自身只计一次）。
import "core"

for p in cells():
    let v = at(x, p)
    let cnt = 0
    for q in row(row_of(p)):
        let cnt = cnt + b2i(at(x, q) == v)
    for q in col(col_of(p)):
        if row_of(q) != row_of(p):
            let cnt = cnt + b2i(at(x, q) == v)
    v == cnt
