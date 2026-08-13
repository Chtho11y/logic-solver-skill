# symmarea — 对称码牌
# 相邻区域面积不同；数字=面积；每区 180° 旋转对称（中心可为格心/边心/顶点）。

import "place2"

neighbour_sizes_differ(c)
region_size_clue(c, n)

for p in cells():
    if is_root(c, p):
        has_180_sym(c, p)
