# 涂黑格互不相邻、留白连通；任一横段/纵段留白不得穿过两个以上区域边界；
# 白圈恰和一个涂黑格接触，黑圈恰和两个涂黑格接触。
import "shading"
import "regions"

island_rule(x)
no_white_crossing_3_regions(x)

for p in clue_cells(o):
    if at(o, p) == 1:
        n_adj8(x, p, 1) == 1
    else:
        n_adj8(x, p, 1) == 2
