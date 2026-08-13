# gokigen — 斜线迷宫
# 每格一条对角线，整体无环。顶点数字=引出的斜线数。
# g: 1=╲ 2=╱；par/rk 为森林父指针。

import "fill2"

for p in cells():
    let r = row_of(p)
    let c = col_of(p)
    let nw = corner(r, c)
    let ne = corner(r, c + 1)
    let sw = corner(r + 1, c)
    let se = corner(r + 1, c + 1)
    at(g, p) == 1 => (at(par, nw) == 1 and at(rk, nw) > at(rk, se)) or (at(par, se) == 4 and at(rk, se) > at(rk, nw))
    at(g, p) == 2 => (at(par, ne) == 2 and at(rk, ne) > at(rk, sw)) or (at(par, sw) == 3 and at(rk, sw) > at(rk, ne))

for v in corners():
    let r = row_of(v)
    let c = col_of(v)
    if r < rows.size and c < cols.size:
        at(par, v) == 1 => at(g, cell(r, c)) == 1
    else:
        at(par, v) != 1
    if r < rows.size and c > 0:
        at(par, v) == 2 => at(g, cell(r, c - 1)) == 2
    else:
        at(par, v) != 2
    if r > 0 and c < cols.size:
        at(par, v) == 3 => at(g, cell(r - 1, c)) == 2
    else:
        at(par, v) != 3
    if r > 0 and c > 0:
        at(par, v) == 4 => at(g, cell(r - 1, c - 1)) == 1
    else:
        at(par, v) != 4

for v in clue_cells(n):
    slash_degree(g, v) == at(n, v)
