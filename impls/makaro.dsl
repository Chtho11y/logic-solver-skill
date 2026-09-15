# 非箭头格：区域内 1..N（N = 非箭头格数）；相邻数字不同。
# 箭头指向其正交数字邻格中唯一最大的那个。
import "core"

for reg in regions:
    let nwhite = 0
    for p in reg:
        if not has_value(d, p):
            let nwhite = nwhite + 1
    for p in reg:
        if has_value(d, p):
            at(x, p) == 0
        else:
            at(x, p) >= 1
            at(x, p) <= nwhite
    for p in reg:
        for q in reg:
            if before(p, q):
                if not has_value(d, p):
                    if not has_value(d, q):
                        at(x, p) != at(x, q)

for p in cells():
    for q in adj4(p):
        (at(x, p) != 0 and at(x, q) != 0) => at(x, p) != at(x, q)

for p in clue_cells(d):
    let tgt = step(p, at(d, p))
    if tgt.size == 0:
        false
    else:
        at(x, tgt) != 0
        for q in adj4(p):
            if row_of(q) != row_of(tgt) or col_of(q) != col_of(tgt):
                at(x, q) != 0 => at(x, q) < at(x, tgt)
