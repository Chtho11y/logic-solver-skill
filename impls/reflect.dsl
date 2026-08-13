# reflect — 反射回路
# 仅在十字格自交；经过所有三角形并在该格直角转弯。
# o: 1=三角形 2=十字。d: 0=上右 1=下右 2=下左 3=上左。
# 数字 = 从三角形出发两条臂的格子总数（含本格）。

import "loops2"

cross_loop(e)

for p in cells():
    if has_value(o, p):
        if at(o, p) == 2:
            is_cross(e, p)
        if at(o, p) == 1:
            on_loop(e, p)
            turns(e, p)
            if has_value(d, p):
                if at(d, p) == 0:
                    link_up(e, p) == 1 and link_right(e, p) == 1
                if at(d, p) == 1:
                    link_down(e, p) == 1 and link_right(e, p) == 1
                if at(d, p) == 2:
                    link_down(e, p) == 1 and link_left(e, p) == 1
                if at(d, p) == 3:
                    link_up(e, p) == 1 and link_left(e, p) == 1
    else:
        cdeg(e, p) != 4

for p in clue_cells(n):
    on_loop(e, p)
    let lu = arm_used_len(e, p, UP)
    let ld = arm_used_len(e, p, DOWN)
    let ll = arm_used_len(e, p, LEFT)
    let lr = arm_used_len(e, p, RIGHT)
    lu + ld + ll + lr - 1 == at(n, p)
