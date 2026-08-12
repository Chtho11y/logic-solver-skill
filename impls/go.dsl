# 有黑圈的格子涂黑，有白圈的格子留白；
# 圆圈里的数字 = 与其所在同色连通组相邻且颜色相反的总格数（「气」）。
import "shading"

for p in clue_cells(o):
    if at(o, p) == 2:
        is_black(x, p)
    else:
        is_white(x, p)
