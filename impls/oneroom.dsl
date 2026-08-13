# 涂黑格互不相邻、留白连通；每个区域内的留白格也需连通；
# 数字 = 此区域内涂黑格数；任意两个相邻区域之间至多一对相邻留白格穿过边界。
import "shading"
import "regions"

island_rule(x)
region_black_count(x, n)

for reg in regions:
    cc_count_in(x, 0, reg) <= 1

for ra in regions:
    for rb in regions:
        if region_id(ra[0]) < region_id(rb[0]):
            doors_between(x, ra, rb) <= 1

def doors_between(x, ra, rb):
    let rid = region_id(rb[0])
    let total = 0
    for p in ra:
        for q in adj4(p):
            if region_id(q) == rid:
                let total = total + b2i(is_white(x, p) and is_white(x, q))
    return total
