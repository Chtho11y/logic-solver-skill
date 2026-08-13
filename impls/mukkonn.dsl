# mukkonn — 四向回路
# 回路经过所有格子。若回路从带数字的三角形所指方向离开此格，
# 则沿该方向直行恰好 n 格（不含本格）后转弯。

import "loops"

full_loop(e)

for p in clue_cells(n):
    if has_value(d, p):
        link_dir(e, p, at(d, p)) == 1 => arm_len(e, p, at(d, p)) == at(n, p)
