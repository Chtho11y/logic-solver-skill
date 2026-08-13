# midloop — 中点回路
# 回路笔直经过每个黑点，且该点是其所在直线段的中点。

import "loops"

cloop(e)

for p in clue_cells(o):
    on_loop(e, p)
    goes_straight(e, p)
    goes_horizontal(e, p) => arm_len(e, p, LEFT) == arm_len(e, p, RIGHT)
    goes_vertical(e, p) => arm_len(e, p, UP) == arm_len(e, p, DOWN)
