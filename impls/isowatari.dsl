# 每个涂黑连通组均为 N 格骨牌（N 由 param("n") 给出）；留白格连通；
# 黑圈格必须涂黑，白圈格必须留白；无全白 2x2。
import "shading"

groups_of_size(x, 1, param("n"))
connected(x, 0)
no2x2(x, 0)

for p in clue_cells(o):
    if at(o, p) == 2:
        is_black(x, p)
    else:
        is_white(x, p)
