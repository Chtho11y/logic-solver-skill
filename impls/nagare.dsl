# nagare — 吹风机回路
# 不经过黑格。白格上的黑箭头：回路沿该轴直行。
# 风扇（黑格上的箭头）下风格子若在回路上则必须含顺风连线。
# 有向“逆风/进入后转向”未编码。

import "loops2"

cloop(e)

for p in cells():
    if marked(w, p):
        off_loop(e, p)

for p in clue_cells(d):
    if not marked(w, p):
        on_loop(e, p)
        goes_straight(e, p)
        link_dir(e, p, at(d, p)) == 1
    else:
        let alive = true
        for q in dir(p, at(d, p)):
            if marked(w, q):
                let alive = false
            if alive:
                on_loop(e, q) => link_dir(e, q, at(d, p)) == 1
