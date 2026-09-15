# 每个数字等于它在所在行和列中出现的次数（自身只计一次）。
import "core"

def simplegako(x):
    for p in cells():
        let v = x[p]
        let cnt = 0
        for q in row(row_of(p)):
            let cnt = cnt + b2i(x[q] == v)
        for q in col(col_of(p)):
            if row_of(q) != row_of(p):
                let cnt = cnt + b2i(x[q] == v)
        v == cnt

simplegako(x)
