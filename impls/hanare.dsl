# hanare — 差距一致
# 每区一格填面积。同行/列中间无其他数字时，中间空格数等于两数之差。

import "fill2"

for p in cells():
    at(x, p) == 0 or at(x, p) == region_of(p).size

for reg in regions:
    num_eq(x[reg], reg.size) == 1

for r in rows:
    for p in r:
        for q in r:
            if col_of(p) < col_of(q):
                let between = 0
                let gap = 0
                for s in r:
                    if col_of(p) < col_of(s) and col_of(s) < col_of(q):
                        let between = between + b2i(at(x, s) > 0)
                        let gap = gap + 1
                at(x, p) > 0 and at(x, q) > 0 and between == 0 => gap == abs(at(x, p) - at(x, q))

for c in cols:
    for p in c:
        for q in c:
            if row_of(p) < row_of(q):
                let between = 0
                let gap = 0
                for s in c:
                    if row_of(p) < row_of(s) and row_of(s) < row_of(q):
                        let between = between + b2i(at(x, s) > 0)
                        let gap = gap + 1
                at(x, p) > 0 and at(x, q) > 0 and between == 0 => gap == abs(at(x, p) - at(x, q))
