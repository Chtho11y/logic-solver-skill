# 分成正方形；顶点处不能四区相会；数字 = 所在正方形边长。
import "regions"

def squarejam(c, n):
    regions_are_squares(c)
    no_four_regions_at_vertex(c)
    for p in clue_cells(n):
        region_width(c, p) == n[p]

squarejam(c, n)
