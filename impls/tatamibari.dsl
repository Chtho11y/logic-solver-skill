# tatamibari — 榻榻米
# 分成若干长方形，每区恰好一个符号。顶点不能同时是四个长方形的一角。
# s: 1=横线(宽>高) 2=竖线(高>宽) 3=加号(正方形)

import "regions"

regions_are_rectangles(c)
one_clue_per_region(c, s)
no_four_meet(c)

for p in clue_cells(s):
    let w = region_width(c, p)
    let h = region_height(c, p)
    if at(s, p) == 1:
        w > h
    if at(s, p) == 2:
        h > w
    if at(s, p) == 3:
        w == h
