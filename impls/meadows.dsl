# 分成正方形；每个区域恰好一个黑圈。
import "regions"

regions_are_squares(c)
one_clue_per_region(c, o)
for p in clue_cells(o):
    region_width(c, p) == region_height(c, p)
