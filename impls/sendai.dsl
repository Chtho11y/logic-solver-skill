# sendai — 宫城县仙台市
# 把给定县再分成市。每市须与另一个大小、方向均相同（平移全等）的市相邻。
# 数字 = 该县分成的市的个数。

import "place2"

for p in cells():
    for q in adj4(p):
        if not same_region(p, q):
            at(c, p) != at(c, q)

for p in clue_cells(n):
    let cities = 0
    for q in region_of(p):
        let cities = cities + b2i(is_root(c, q))
    cities == at(n, p)

for p in cells():
    if is_root(c, p):
        let found = false
        for q in cells():
            if is_root(c, q):
                let found = found or ((row_of(p) != row_of(q) or col_of(p) != col_of(q)) and regions_touch(c, p, q) and translation_congruent(c, p, q))
        found
