# doppelblock — 双黑格
# 每行每列 1..N-2 各一次及两个黑格。盘外数字=两黑格之间所有数字之和。

import "fill2"

let n = board_n()

for p in cells():
    at(x, p) >= 0
    at(x, p) <= n - 2

for r in rows:
    num_eq(x[r], 0) == 2
    for p in r:
        let v = col_of(p) + 1
        if v <= n - 2:
            num_eq(x[r], v) == 1
        if v > n - 2:
            num_eq(x[r], v) == 0

for c in cols:
    num_eq(x[c], 0) == 2
    for p in c:
        let v = row_of(p) + 1
        if v <= n - 2:
            num_eq(x[c], v) == 1
        if v > n - 2:
            num_eq(x[c], v) == 0

for i in rows:
    let k = side_clue("left", row_of(i[0]))
    if not no_clue(k):
        let s = 0
        let state = 0
        for p in i:
            let isb = b2i(at(x, p) == 0)
            let s = s + ite(state == 1, ite(isb == 1, 0, at(x, p)), 0)
            let state = ite(isb == 1, state + 1, state)
        s == k

for j in cols:
    let k = side_clue("top", col_of(j[0]))
    if not no_clue(k):
        let s = 0
        let state = 0
        for p in j:
            let isb = b2i(at(x, p) == 0)
            let s = s + ite(state == 1, ite(isb == 1, 0, at(x, p)), 0)
            let state = ite(isb == 1, state + 1, state)
        s == k
