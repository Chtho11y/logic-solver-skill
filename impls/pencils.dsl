# pencils — 铅笔
# 每支笔 = 1×N 笔杆 + 1×1 笔头 + N 格笔迹。数字在笔杆内且等于 N。
# 全盘被铅笔（含笔迹）覆盖。

import "place2"

# k: 0=笔杆 1=笔头 2=笔迹。同一区域 k 构成一支笔。
for p in cells():
    let nshaft = count_where(cells(), fn (q) -> at(c, q) == at(c, p) and at(k, q) == 0)
    let ntip = count_where(cells(), fn (q) -> at(c, q) == at(c, p) and at(k, q) == 1)
    let ntrail = count_where(cells(), fn (q) -> at(c, q) == at(c, p) and at(k, q) == 2)
    ntip == 1
    nshaft >= 1
    nshaft == ntrail
    at(c.size, p) == 2 * nshaft + 1

# 笔杆在同一行或同一列且连续（外接矩形面积 = 笔杆格数）。
for p in cells():
    if at(k, p) == 0:
        let minr = row_of(p)
        let maxr = row_of(p)
        let minc = col_of(p)
        let maxc = col_of(p)
        for q in cells():
            let here = at(c, q) == at(c, p) and at(k, q) == 0
            let minr = ite(here and row_of(q) < minr, row_of(q), minr)
            let maxr = ite(here and row_of(q) > maxr, row_of(q), maxr)
            let minc = ite(here and col_of(q) < minc, col_of(q), minc)
            let maxc = ite(here and col_of(q) > maxc, col_of(q), maxc)
        let ns = count_where(cells(), fn (q) -> at(c, q) == at(c, p) and at(k, q) == 0)
        (maxr - minr + 1) * (maxc - minc + 1) == ns
        maxr - minr == 0 or maxc - minc == 0

# 笔头与笔杆相邻，且不与另一笔头/其它笔杆乱接：笔头恰有一个同区笔杆邻居。
for p in cells():
    if at(k, p) == 1:
        count_where(adj4(p), fn (q) -> at(c, q) == at(c, p) and at(k, q) == 0) == 1
        count_where(adj4(p), fn (q) -> at(c, q) == at(c, p) and at(k, q) == 2) == 1

# 笔迹宽度为一，且只与笔头/笔迹相连。
for p in cells():
    if at(k, p) == 2:
        count_where(adj4(p), fn (q) -> at(c, q) == at(c, p) and at(k, q) != 0) <= 2
        for q in adj4(p):
            at(c, q) == at(c, p) => at(k, q) != 0

for p in clue_cells(n):
    at(k, p) == 0
    count_where(cells(), fn (q) -> at(c, q) == at(c, p) and at(k, q) == 0) == at(n, p)
