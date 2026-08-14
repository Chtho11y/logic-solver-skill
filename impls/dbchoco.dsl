# dbchoco — 双巧克力
# 每区一组连通灰格与一组连通白格，两组相邻且全等。数字=一组的面积（区域一半）。

import "place2"

at_most_one_clue_per_region(c, n)

for p in cells():
    if is_root(c, p):
        let ng = color_count_in(c, g, p, 1)
        let nw = color_count_in(c, g, p, 0)
        ng == nw
        ng >= 1
        color_pairs_in(c, g, p, 1) >= ng - 1
        color_pairs_in(c, g, p, 0) >= nw - 1
        let touch = false
        for q in cells():
            let touch = touch or any_where(adj4(q), fn (r) -> at(c, q) == at(c, p) and at(c, r) == at(c, p) and at(g, q) != at(g, r))
        touch

for p in clue_cells(n):
    at(c.size, p) == 2 * at(n, p)
