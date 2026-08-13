# hidato — 一笔画
# 填入 1..N 各一次（N=总格数）。相邻数字（差为 1）必须在八邻域内。

import "fill"

let nmax = rows.size * cols.size
for p in cells():
    at(x, p) >= 1
    at(x, p) <= nmax

distinct(x)

for p in clue_cells(n):
    at(x, p) == at(n, p)

for p in cells():
    for q in cells():
        if before(p, q):
            let adj = false
            for r in adj8(p):
                let adj = adj or (row_of(r) == row_of(q) and col_of(r) == col_of(q))
            abs(at(x, p) - at(x, q)) == 1 => adj
