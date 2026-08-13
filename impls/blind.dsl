# blind — 盲点
# 每区一个箭头；每行每列四种箭头各一次。
# 箭头不能指向另一个箭头，除非中间有区域边界。

import "fill2"

for p in cells():
    at(a, p) == 8 or at(a, p) <= 3

for r in rows:
    for d in [UP, DOWN, LEFT, RIGHT]:
        num_eq(a[r], d) == 1
for c in cols:
    for d in [UP, DOWN, LEFT, RIGHT]:
        num_eq(a[c], d) == 1

for reg in regions:
    num_eq(a[reg], 8) == reg.size - 1

for p in cells():
    for d in [UP, DOWN, LEFT, RIGHT]:
        let blocked = 0
        let hit = 0
        let prev = p
        for q in dir(p, d):
            if not same_region(prev, q):
                let blocked = 1
            let hit = hit + b2i(blocked == 0 and at(a, q) != 8)
            let prev = q
        at(a, p) == d => hit == 0
