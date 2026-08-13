# castle — 城堡墙
# 回路不经过提示格。白格提示在回路内，黑格提示在回路外。
# 带箭头的数字 = 该方向上回路经过的格子总数。
# o: 1=白格 2=黑格；y=不在回路上（辅助）；ins=在回路内（辅助）。

import "loops"

cloop(e)

for p in cells():
    at(y, p) == b2i(off_loop(e, p))

let ids = cc_id(y)
for p in cells():
    let touch = false
    for b in boundary():
        let touch = touch or (at(y, b) == 1 and at(ids, p) == at(ids, b))
    off_loop(e, p) => at(ins, p) == b2i(not touch)
    on_loop(e, p) => at(ins, p) == 0

for p in clue_cells(o):
    off_loop(e, p)
    if at(o, p) == 1:
        at(ins, p) == 1
    if at(o, p) == 2:
        at(ins, p) == 0

for p in clue_cells(n):
    off_loop(e, p)
    if has_value(d, p):
        let total = 0
        for q in dir(p, at(d, p)):
            let total = total + b2i(on_loop(e, q))
        total == at(n, p)
