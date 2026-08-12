# 涂黑格互不相邻、留白连通；任一横段/纵段留白不得穿过两个以上区域边界；
# 数字 = 此区域内涂黑格数；所有区域的涂黑情况必须 180° 旋转对称。
import "shading"
import "regions"

island_rule(x)
no_white_crossing_3_regions(x)
region_black_count(x, n)

for reg in regions:
    region_half_turn_symmetric(x, reg)

def region_half_turn_symmetric(x, reg):
    let minr = row_of(reg[0])
    let maxr = row_of(reg[0])
    let minc = col_of(reg[0])
    let maxc = col_of(reg[0])
    for p in reg:
        if row_of(p) < minr:
            let minr = row_of(p)
        if row_of(p) > maxr:
            let maxr = row_of(p)
        if col_of(p) < minc:
            let minc = col_of(p)
        if col_of(p) > maxc:
            let maxc = col_of(p)
    for p in reg:
        at(x, p) == at(x, cell(minr + maxr - row_of(p), minc + maxc - col_of(p)))
