# compass — 指南针
# 每个区域恰好一个叉（指南针）。叉上/下/左/右的数字 = 区域内严格更靠上/下/左/右的格数。

import "regions"

one_clue_per_region(c, k)

for p in clue_cells(k):
    if has_value(nu, p):
        region_above(c, p) == at(nu, p)
    if has_value(nd, p):
        region_below(c, p) == at(nd, p)
    if has_value(nl, p):
        region_left_of(c, p) == at(nl, p)
    if has_value(nr, p):
        region_right_of(c, p) == at(nr, p)
