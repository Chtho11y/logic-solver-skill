# shimaguni — 岛国
# 每个区域内涂黑恰好一组连通的格子；不同区域内的涂黑组不相邻；
# 数字表示区域内涂黑格的个数；相邻区域内涂黑格的个数不能相同。

import "shading"
import "regions"

for reg in regions:
    num_eq(x[reg], 1) >= 1

region_black_count(x, n)

for p in cells():
    for q in adj4(p):
        if not same_region(p, q):
            not (is_black(x, p) and is_black(x, q))

# 跨区域黑格不相邻 => 每个黑连通组都落在一个区域内；组数 == 区域数 即每区域恰一组。
cc_count(x, 1) == regions.size

for p in cells():
    for q in adj4(p):
        if region_id(p) < region_id(q):
            num_eq(x[region_of(p)], 1) != num_eq(x[region_of(q)], 1)
