# heteromino — 三格拼版
# 分成三格骨牌，相邻的不平移全等（形状或朝向不同）。

import "place2"

all_regions_size(c, 3)

for p in cells():
    for q in adj4(p):
        at(c, p) != at(c, q) => tromino_type(c, p) != tromino_type(c, q)
