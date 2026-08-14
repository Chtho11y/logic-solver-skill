# sendai — 宫城县仙台市
# 把给定县再分成市。每市须与另一个大小、方向均相同（平移全等）的市相邻。
# 数字 = 该县分成的市的个数。

import "place2"

for p in cells():
    for q in adj4(p):
        if not same_region(p, q):
            at(c, p) != at(c, q)

for p in clue_cells(n):
    count_where(region_of(p), fn (q) -> is_root(c, q)) == at(n, p)

for p in cells():
    if is_root(c, p):
        any_where(cells(), fn (q) -> is_root(c, q) and (row_of(p) != row_of(q) or col_of(p) != col_of(q)) and regions_touch(c, p, q) and translation_congruent(c, p, q))
