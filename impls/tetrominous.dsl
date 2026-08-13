# tetrominous — 四格拼板
# 分成四格骨牌，相邻不全等。字母 = 形状（I=1 O=2 T=3 L=4 S=5）。

import "place2"

all_regions_size(c, 4)

for p in cells():
    for q in adj4(p):
        at(c, p) != at(c, q) => tet_type(c, p) != tet_type(c, q)

for p in clue_cells(s):
    tet_type(c, p) == at(s, p)
