# 分成矩形，每区一个符号；顶点处不能四区相会。
# 1 = 加号（正方形），2 = 横线（宽>高），3 = 竖线（高>宽）。
import "regions"

def tatamibari(c, s):
    regions_are_rectangles(c)
    one_clue_per_region(c, s)
    no_four_regions_at_vertex(c)
    for p in clue_cells(s):
        if s[p] == 1:
            region_width(c, p) == region_height(c, p)
        elif s[p] == 2:
            region_width(c, p) > region_height(c, p)
        else:
            region_height(c, p) > region_width(c, p)

tatamibari(c, s)
