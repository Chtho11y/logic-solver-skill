# slalom — 巡行通关
# 有向回路的无向松弛：不经过黑格，经过圆圈，关卡格直行。
# 圆圈内数字 = 关卡总数。带数字箭头的关卡次序未编码。

import "loops2"

cloop(e)

for p in cells():
    if marked(w, p):
        off_loop(e, p)

for p in clue_cells(o):
    on_loop(e, p)

for p in cells():
    if marked(g, p):
        on_loop(e, p)
        goes_straight(e, p)

for p in clue_cells(n):
    if has_value(o, p):
        count_where(cells(), fn (q) -> marked(g, q)) == at(n, p)
