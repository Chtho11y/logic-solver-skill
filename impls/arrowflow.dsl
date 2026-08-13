# arrowflow — 箭头流动
# 空格放箭头，相同箭头不相邻。沿箭头到达线索格。数字=到达该格的箭头格数。

import "fill2"

arrows_never_leave_board(a)

for p in cells():
    if has_value(n, p):
        at(a, p) == 8
        at(dest, p) == row_of(p) * cols.size + col_of(p)
    else:
        at(a, p) <= 3
        at(dest, p) >= 0
        for q in adj4(p):
            if not has_value(n, q):
                at(a, p) != at(a, q)
        for d in [UP, DOWN, LEFT, RIGHT]:
            let q = step(p, d)
            if q.size == 0:
                at(a, p) != d
            else:
                at(a, p) == d => at(dest, p) == at(dest, q)

for p in clue_cells(n):
    let idx = row_of(p) * cols.size + col_of(p)
    if at(n, p) >= 0:
        num_eq(dest, idx) == at(n, p) + 1
