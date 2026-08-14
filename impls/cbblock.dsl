# cbblock — 组合区块
# 每区恰好包含两个给定虚线块；区域不是长方形；相邻区域不全等。

import "place2"

for p in cells():
    for q in cells():
        if same_region(p, q):
            at(c, p) == at(c, q)

for p in cells():
    if is_root(c, p):
        count_where(regions, fn (reg) -> block_in(c, p, reg)) == 2
        region_notch_count(c, p) >= 1

for p in cells():
    for q in adj4(p):
        if before(p, q):
            at(c, p) != at(c, q) and at(c.size, p) == at(c.size, q) => not freely_congruent(c, p, q)

def block_in(c, p, reg):
    return any_where(reg, fn (q) -> at(c, q) == at(c, p))
