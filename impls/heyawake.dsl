# heyawake — 数间
# 涂黑格互不相邻、留白连通；任意一横段或纵段留白格不能穿过两个以上区域边界；
# 数字表示此区域内涂黑格的个数。

import "shading"
import "regions"

island_rule(x)
region_black_count(x, n)
no_white_crossing_3_regions(x)
