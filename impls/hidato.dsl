# 填入 1..N 各一次（N = 总格数）；连续数字必须八邻域相邻。
import "core"

def hidato(x):
    let n = rows.size * cols.size
    for p in cells():
        x[p] >= 1
        x[p] <= n
    for p in cells():
        for q in cells():
            if before(p, q):
                x[p] != x[q]
    for p in cells():
        let ok = b2i(x[p] == n)
        for q in adj8(p):
            let ok = ok + b2i(x[q] == x[p] + 1)
        ok >= 1

hidato(x)
