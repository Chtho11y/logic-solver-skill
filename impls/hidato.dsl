# 填入 1..N 各一次（N = 总格数）；连续数字必须八邻域相邻。
import "core"

let n = rows.size * cols.size
for p in cells():
    at(x, p) >= 1
    at(x, p) <= n
for p in cells():
    for q in cells():
        if before(p, q):
            at(x, p) != at(x, q)
for p in cells():
    let ok = b2i(at(x, p) == n)
    for q in adj8(p):
        let ok = ok + b2i(at(x, q) == at(x, p) + 1)
    ok >= 1
