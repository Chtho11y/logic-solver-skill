# narrow — narrow
# 非长方形区域，每区恰一符号。同符号区域形状不同（旋转翻转视为相同）。
# 不允许 2×2 四格都属于同符号区域。

import "place2"

one_clue_per_region(c, s)

for p in cells():
    region_notch_count(c, p) >= 1

for p in clue_cells(s):
    for q in clue_cells(s):
        if before(p, q):
            if at(s, p) == at(s, q):
                not freely_congruent(c, p, q)

for w in slide(2, 2):
    let same = true
    for p in w:
        for q in w:
            let sp = 0
            let sq = 0
            for a in clue_cells(s):
                let sp = ite(at(c, a) == at(c, p), at(s, a), sp)
                let sq = ite(at(c, a) == at(c, q), at(s, a), sq)
            let same = same and (sp == sq)
    not same
