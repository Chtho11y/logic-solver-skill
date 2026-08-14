# nagenawa — 套索
# 若干矩形回路，可交叉不可共角。数字 = 区域内至少被一条回路经过的格数。

import "loops2"
import "regions"

rectangular_loops(e)

for p in clue_cells(n):
    count_where(region_of(p), fn (q) -> on_drawn_rect(e, q)) == at(n, p)
