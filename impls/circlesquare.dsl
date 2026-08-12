# 涂黑格连通、无全黑 2x2；黑圈格必须涂黑，白圈格必须留白；
# 每一组留白的连通组都是正方形。
import "shading"

wall_rule(x)
# 正方形的必要条件：留白连通组是长方形（无 L 形拐角）。
is_rect_group(x, 0)

for p in clue_cells(o):
    if at(o, p) == 2:
        is_black(x, p)
    else:
        is_white(x, p)
