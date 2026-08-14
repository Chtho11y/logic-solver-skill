# kropki — 黑白点
# 拉丁方。全部黑白点已给出。白点差 1，黑点比 1:2。相邻 1 与 2 可用任一种点。

import "fill2"

latin_n(x, board_n())

for p in cells():
    let q = shift(p, 0, 1)
    if in_grid(p, 0, 1):
        let e = between_v_edge(p, q)
        let consec = kropki_consec(at(x, p), at(x, q))
        let double = kropki_double(at(x, p), at(x, q))
        if has_value(o, e):
            if at(o, e) == 1:
                consec
            if at(o, e) == 2:
                double
        else:
            not consec and not double
    let q2 = shift(p, 1, 0)
    if in_grid(p, 1, 0):
        let e = between_h_edge(p, q2)
        let consec = kropki_consec(at(x, p), at(x, q2))
        let double = kropki_double(at(x, p), at(x, q2))
        if has_value(o, e):
            if at(o, e) == 1:
                consec
            if at(o, e) == 2:
                double
        else:
            not consec and not double
