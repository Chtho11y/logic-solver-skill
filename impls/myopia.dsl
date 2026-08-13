# myopia — 近视回路
# 连接相邻圆点画一条不自交回路。
# a 为方向位掩码（1=上 2=下 4=左 8=右）：箭头指向所有离此格最近的回路边所在方向。

import "loops"

loop(e)

for p in clue_cells(a):
    let du = nearest_loop_dist(e, p, UP)
    let dd = nearest_loop_dist(e, p, DOWN)
    let dl = nearest_loop_dist(e, p, LEFT)
    let dr = nearest_loop_dist(e, p, RIGHT)
    let inf = rows.size + cols.size + 1
    let m = inf
    let m = ite(du > 0 and du < m, du, m)
    let m = ite(dd > 0 and dd < m, dd, m)
    let m = ite(dl > 0 and dl < m, dl, m)
    let m = ite(dr > 0 and dr < m, dr, m)
    let bits = at(a, p)
    let has_u = bits % 2 == 1
    let has_d = (bits / 2) % 2 == 1
    let has_l = (bits / 4) % 2 == 1
    let has_r = (bits / 8) % 2 == 1
    if has_u:
        du > 0 and du == m
    if not has_u:
        du == 0 or du > m
    if has_d:
        dd > 0 and dd == m
    if not has_d:
        dd == 0 or dd > m
    if has_l:
        dl > 0 and dl == m
    if not has_l:
        dl == 0 or dl > m
    if has_r:
        dr > 0 and dr == m
    if not has_r:
        dr == 0 or dr > m
