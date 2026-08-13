# icebarn — 冰宫游弋
# 从 IN 到 OUT 的路径。白格不自交；冰格不转弯但可十字自交。每组冰区至少经过一次。
# 箭头：路径沿该轴穿过该格（自交时方向感为松弛）。

import "paths2"
import "regions"

no_outer_links(e)
connect_links(e)

for p in cells():
    if has_value(m, p):
        cdeg(e, p) == 1
        if has_value(d, p):
            link_dir(e, p, at(d, p)) == 1 or link_dir(e, p, opposite_dir(at(d, p))) == 1
    elif has_value(g, p):
        ice_cell_ok(e, p)
    else:
        cdeg(e, p) == 0 or cdeg(e, p) == 2

for p in clue_cells(d):
    if not has_value(m, p):
        let axis = (at(d, p) == UP or at(d, p) == DOWN)
        if axis:
            goes_vertical(e, p) or cdeg(e, p) == 4
        else:
            goes_horizontal(e, p) or cdeg(e, p) == 4

for reg in regions:
    let ng = 0
    for p in reg:
        if has_value(g, p):
            let ng = ng + 1
    if ng > 0:
        region_visited_cells(e, reg) >= 1
