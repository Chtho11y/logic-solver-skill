# icelom — 冰宫巡游
# 从 IN 到 OUT 经过全部白格。冰格不转弯但可自交。数字顺序未编码（冰面可走两次）。

import "paths2"

no_outer_links(e)
connect_links(e)

for p in cells():
    if has_value(m, p):
        cdeg(e, p) == 1
    elif has_value(g, p):
        ice_cell_ok(e, p)
    else:
        cdeg(e, p) == 2
