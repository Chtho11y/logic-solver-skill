# 拉丁方 1..N。白点差 1，黑点比 1:2；无点则既非连续也非倍半。1 与 2 两种点都行。
import "fill"

latin_1_to_n(x)

for e in clue_cells(d):
    let cs = cell_of(e)
    if cs.size == 2:
        let a = x[cs[0]]
        let b = x[cs[1]]
        if d[e] == 1:
            kropki_white(a, b)
        else:
            kropki_black(a, b)
    else:
        false

for p in cells():
    let q = shift(p, 0, 1)
    if q.size == 1:
        let e = edge("V", row_of(p), col_of(p) + 1)
        if not has_value(d, e):
            not kropki_white(x[p], x[q]) and not kropki_black(x[p], x[q])
    let q2 = shift(p, 1, 0)
    if q2.size == 1:
        let e = edge("H", row_of(p) + 1, col_of(p))
        if not has_value(d, e):
            not kropki_white(x[p], x[q2]) and not kropki_black(x[p], x[q2])
