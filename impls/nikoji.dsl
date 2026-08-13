# nikoji — 异同分割
# 每区恰一字母。同字母区域平移全等（含字母相对位置）；异字母不能以任何方式全等。

import "place2"

one_clue_per_region(c, s)

for p in clue_cells(s):
    for q in clue_cells(s):
        if before(p, q):
            if at(s, p) == at(s, q):
                translation_congruent(c, p, q)
            if at(s, p) != at(s, q):
                not freely_congruent(c, p, q)
