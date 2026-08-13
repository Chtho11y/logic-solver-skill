# gaps — 空隙
# 每行每列两颗星；星不能接触（含对角）。盘外数字 = 两星之间的空格数。

import "core"
import "outside"

for r in rows:
    num_eq(x[r], 1) == 2
for c in cols:
    num_eq(x[c], 1) == 2

for p in cells():
    at(x, p) == 1 => n_adj8(x, p, 1) == 0

for i in rows:
    let k = side_clue("left", row_of(i[0]))
    if not no_clue(k):
        let gap = 0
        for p in i:
            for q in i:
                if col_of(q) > col_of(p):
                    let gap = gap + b2i(at(x, p) == 1 and at(x, q) == 1) * (col_of(q) - col_of(p) - 1)
        gap == k

for j in cols:
    let k = side_clue("top", col_of(j[0]))
    if not no_clue(k):
        let gap = 0
        for p in j:
            for q in j:
                if row_of(q) > row_of(p):
                    let gap = gap + b2i(at(x, p) == 1 and at(x, q) == 1) * (row_of(q) - row_of(p) - 1)
        gap == k
