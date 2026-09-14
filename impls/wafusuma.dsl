# Fillomino 邻区面积不同；格线上数字 = 两侧区域面积之和（两侧必须不同区）。
import "regions"

neighbour_sizes_differ(c)
for e in clue_cells(k):
    let cs = cell_of(e)
    if cs.size == 2:
        at(c, cs[0]) != at(c, cs[1])
        at(c.size, cs[0]) + at(c.size, cs[1]) == at(k, e)
    else:
        false
