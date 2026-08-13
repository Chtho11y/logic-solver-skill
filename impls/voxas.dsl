# voxas — 二三分割
# 分成面积为 2 或 3 的长方形。高为 1 称横向，宽为 1 称纵向。
# 给定边界上的圆点：1白=面积和朝向都相同，3灰=恰有一个相同，2黑=两者均不同。

import "place2"

regions_are_rectangles(c)

for p in cells():
    at(c.size, p) == 2 or at(c.size, p) == 3

for e in clue_cells(o):
    let sides = cell_of(e)
    sides.size == 2
    for p in sides:
        for q in sides:
            if before(p, q):
                at(c, p) != at(c, q)
                let same_area = at(c.size, p) == at(c.size, q)
                let hp = region_height(c, p) == 1
                let hq = region_height(c, q) == 1
                let same_dir = hp == hq
                if at(o, e) == 1:
                    same_area and same_dir
                if at(o, e) == 2:
                    not same_area and not same_dir
                if at(o, e) == 3:
                    (same_area or same_dir) and not (same_area and same_dir)
