# 涂黑格连通、无全黑 2x2；黑圈格必须涂黑，白圈格必须留白；
# 每一组留白的连通组都是正方形。
import "shading"

wall_rule(x)
square_groups(x, 0)

for p in clue_cells(o):
    if at(o, p) == 2:
        is_black(x, p)
    else:
        is_white(x, p)
