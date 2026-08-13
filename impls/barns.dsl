# barns — 冰宫回路
# 经过所有格子。不能穿过粗格线。冰格不能转弯但可自交；白格不能自交。

import "loops2"

connect_links(e)

for p in cells():
    if marked(t, p):
        let d = cdeg(e, p)
        d == 2 or d == 4
        d == 2 => goes_straight(e, p)
    else:
        cdeg(e, p) == 2

for k in clue_cells(w):
    at(e, k) == 0
