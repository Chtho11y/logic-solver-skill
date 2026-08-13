# pipelink — 管道回路
# 经过所有格子，允许十字交叉但不能在交叉处转弯。
# s: 1=横 2=竖 3=交叉 4=上左 5=上右 6=下左 7=下右。

import "loops2"

full_cross_loop(e)

for p in clue_cells(s):
    if at(s, p) == 1:
        goes_horizontal(e, p)
        cdeg(e, p) == 2
    if at(s, p) == 2:
        goes_vertical(e, p)
        cdeg(e, p) == 2
    if at(s, p) == 3:
        is_cross(e, p)
    if at(s, p) == 4:
        link_up(e, p) == 1 and link_left(e, p) == 1
        cdeg(e, p) == 2
    if at(s, p) == 5:
        link_up(e, p) == 1 and link_right(e, p) == 1
        cdeg(e, p) == 2
    if at(s, p) == 6:
        link_down(e, p) == 1 and link_left(e, p) == 1
        cdeg(e, p) == 2
    if at(s, p) == 7:
        link_down(e, p) == 1 and link_right(e, p) == 1
        cdeg(e, p) == 2
