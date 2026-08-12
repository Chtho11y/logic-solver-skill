# ripple — 涟漪效应
# 每个区域里包含数字 1~N；同行列中两个相同数字之间的格数必须 >= 该数字。

import "fill"

region_1_to_n(x)

for r in rows:
    for p in r:
        for q in r:
            let d = col_of(q) - col_of(p)
            if d > 0:
                at(x, p) == at(x, q) => at(x, p) <= d - 1

for c in cols:
    for p in c:
        for q in c:
            let d = row_of(q) - row_of(p)
            if d > 0:
                at(x, p) == at(x, q) => at(x, p) <= d - 1
