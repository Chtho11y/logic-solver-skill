# pentominous — 五格拼板
# 分成五格骨牌，相邻不全等。字母 = 骨牌形状（F=1 I=2 L=3 N=4 P=5 T=6 U=7 V=8 W=9 X=10 Y=11 Z=12）。

import "place2"

all_regions_size(c, 5)

for p in cells():
    for q in adj4(p):
        at(c, p) != at(c, q) => pent_type(c, p) != pent_type(c, q)

for p in clue_cells(s):
    pent_type(c, p) == at(s, p)
