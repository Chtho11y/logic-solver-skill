# geradeweg — 直线回路
# 回路经过所有带圈格。与圈相交的每条直线段长度等于圈内数字。

import "loops"

cloop(e)

for p in clue_cells(o):
    on_loop(e, p)

for p in clue_cells(n):
    on_loop(e, p)
    goes_straight(e, p) => full_straight_len(e, p) == at(n, p)
    for d in [UP, DOWN, LEFT, RIGHT]:
        turns(e, p) and link_dir(e, p, d) == 1 => 1 + arm_len(e, p, d) == at(n, p)
