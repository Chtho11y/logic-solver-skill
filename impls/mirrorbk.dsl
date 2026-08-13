# mirrorbk — 镜像区块
# 每区至多一个数字=面积。粗线镜子两侧两区关于该镜子轴对称。

import "place2"

at_most_one_clue_per_region(c, n)
region_size_clue(c, n)

for e in clue_cells(m):
    let sides = cell_of(e)
    sides.size == 2
    for p in sides:
        for q in sides:
            if before(p, q):
                at(c, p) != at(c, q)
                mirror_image(c, p, q, p, q)
