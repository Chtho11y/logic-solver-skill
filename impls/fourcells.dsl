# 分成四格骨牌；数字 = 此格四条边中属于区域边界（含盘边）的条数。
import "regions"
import "loops"

all_regions_size(c, 4)
for p in clue_cells(n):
    cell_edge_count(c.border, p) == n[p]
