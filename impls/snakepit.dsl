# snakepit — 蛇窝
# 相邻区域面积不同；数字=面积。区域是宽为一、长度≥2 的蛇（恰两端点，无 2x2）。
# 圆圈是蛇的一端；灰格不是一端。

import "regions"

neighbour_sizes_differ(c)
region_size_clue(c, n)

for w in slide(2, 2):
    for p in w:
        num_eq(c[w], at(c, p)) != 4

for p in cells():
    at(c.size, p) >= 2
    region_deg(c, p) <= 2
    region_end_count(c, p) == 2

for p in clue_cells(o):
    region_deg(c, p) == 1

for p in clue_cells(g):
    region_deg(c, p) != 1
