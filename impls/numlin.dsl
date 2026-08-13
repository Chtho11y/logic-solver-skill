# numlin — 数连
# 相同数字之间画一条不交叉的正交路径；端点交叉也不允许。

import "loops"

for p in cells():
    let up = shift(p, -1, 0)
    let down = shift(p, 1, 0)
    let left = shift(p, 0, -1)
    let right = shift(p, 0, 1)
    if up.size == 0:
        link_up(e, p) == 0
    if down.size == 0:
        link_down(e, p) == 0
    if left.size == 0:
        link_left(e, p) == 0
    if right.size == 0:
        link_right(e, p) == 0

for p in cells():
    if has_value(n, p):
        at(x, p) == at(n, p)
        cdeg(e, p) == 1
    else:
        (at(x, p) == 0 and cdeg(e, p) == 0) or (at(x, p) != 0 and cdeg(e, p) == 2)

for p in cells():
    for q in adj4(p):
        if before(p, q):
            link_between(e, p, q) == 1 => at(x, p) == at(x, q) and at(x, p) != 0

for p in clue_cells(n):
    cc_count(x, at(n, p)) == 1
