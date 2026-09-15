# fillomino — 码牌
# 沿虚格线把盘面分成若干区域，任意两个相邻区域面积不同；数字表示其所在区域面积。

import "regions"

def fillomino(c, n):
    neighbour_sizes_differ(c)
    region_size_clue(c, n)

fillomino(c, n)
