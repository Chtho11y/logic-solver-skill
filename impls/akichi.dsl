# 涂黑格互不相邻、留白连通；任一横段/纵段留白不得穿过两个以上区域边界；
# 数字 = 此区域内最大留白连通组的面积。
import "shading"
import "regions"

island_rule(x)
no_white_crossing_3_regions(x)

for p in clue_cells(n):
    let reg = region_of(p)
    let mx = 0
    for q in reg:
        let mx = max(mx, ite(is_white(x, q), cc_size_in(x, q, reg), 0))
    mx == at(n, p)
