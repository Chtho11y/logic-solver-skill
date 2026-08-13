# squarejam — 正方密铺
# 沿虚格线把盘面分成若干个正方形区域。每个顶点不能同时是四个正方形的一角。
# 数字表示其所在的正方形的边长。

import "regions"

regions_are_squares(c)
no_four_meet(c)
for p in clue_cells(n):
    region_width(c, p) == at(n, p)
