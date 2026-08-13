# kropki-pairs — 黑白点对
# 拉丁方。白点差 1，黑点比 1:2。未给出的点不约束。

import "fill2"

latin_n(x, board_n())

for p in cells():
    let q = shift(p, 0, 1)
    if q.size > 0:
        let e = between_v_edge(p, q)
        if has_value(o, e):
            if at(o, e) == 1:
                kropki_consec(at(x, p), at(x, q))
            if at(o, e) == 2:
                kropki_double(at(x, p), at(x, q))
    let q2 = shift(p, 1, 0)
    if q2.size > 0:
        let e = between_h_edge(p, q2)
        if has_value(o, e):
            if at(o, e) == 1:
                kropki_consec(at(x, p), at(x, q2))
            if at(o, e) == 2:
                kropki_double(at(x, p), at(x, q2))
