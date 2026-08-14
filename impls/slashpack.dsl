# slashpack — 斜线分区
# 空格可画对角线（1=\  2=/）把盘面分成区域。每区含 1..N 各一次（N=盘面最大数字）。
# 用格内两三角编号 + 邻边一致作为连通的合法松弛。

import "place2"

for p in cells():
    at(s, p) == 0 or at(s, p) == 1 or at(s, p) == 2
    if has_value(n, p):
        at(s, p) == 0
    at(s, p) == 0 => at(u, p) == at(v, p)

# \ : u=SW v=NE； / : u=NW v=SE；无斜线 u=v。v 总管右缘，u 总管左缘。
for p in cells():
    if in_grid(p, 0, 1):
        at(v, p) == at(u, shift(p, 0, 1))
    if in_grid(p, 1, 0):
        let dn = shift(p, 1, 0)
        # p 的下缘：无斜线 = u；\ = u(SW)；/ = v(SE)
        let pbot = ite(at(s, p) == 2, at(v, p), at(u, p))
        # dn 的上缘：无斜线 = u；\ = v(NE)；/ = u(NW)
        let qtop = ite(at(s, dn) == 1, at(v, dn), at(u, dn))
        pbot == qtop

let nmax = 1
for p in clue_cells(n):
    if at(n, p) > nmax:
        let nmax = at(n, p)

for k in [1, 2, 3, 4, 5, 6, 7, 8]:
    if k <= nmax:
        let cntk = count_where(clue_cells(n), fn (p) -> at(n, p) == k)
        let cnt1 = count_where(clue_cells(n), fn (p) -> at(n, p) == 1)
        cntk == cnt1

for p in clue_cells(n):
    for k in [1, 2, 3, 4, 5, 6, 7, 8]:
        if k <= nmax:
            let cnt = count_where(clue_cells(n), fn (q) -> at(u, q) == at(u, p) and at(n, q) == k)
            cnt == 1
