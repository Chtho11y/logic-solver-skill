# 每区恰好填一个等于区域面积的数；同行/列且中间无其他数字时，中间空格数 = 两数之差。
import "core"

for reg in regions:
    let nz = 0
    for p in reg:
        let nz = nz + b2i(x[p] != 0)
        x[p] == 0 or x[p] == reg.size
    nz == 1

for p in cells():
    for q in cells():
        if row_of(p) == row_of(q):
            if col_of(p) < col_of(q):
                let blocked = 0
                for t in row(row_of(p)):
                    if col_of(p) < col_of(t):
                        if col_of(t) < col_of(q):
                            let blocked = blocked + b2i(x[t] != 0)
                (x[p] != 0 and x[q] != 0 and blocked == 0) => (col_of(q) - col_of(p) - 1 == abs(x[p] - x[q]))
        if col_of(p) == col_of(q):
            if row_of(p) < row_of(q):
                let blocked = 0
                for t in col(col_of(p)):
                    if row_of(p) < row_of(t):
                        if row_of(t) < row_of(q):
                            let blocked = blocked + b2i(x[t] != 0)
                (x[p] != 0 and x[q] != 0 and blocked == 0) => (row_of(q) - row_of(p) - 1 == abs(x[p] - x[q]))
