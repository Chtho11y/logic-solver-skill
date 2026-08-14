# heavydots — 重点
# 区域不含完整 2×2。每区至多一数字=面积。
# 黑点(2)=顶点恰 3 条区界；白点(1)=恰 4 条。与已标点相邻的未标点不能为 3 或 4 条。

import "place2"

for w in slide(2, 2):
    for p in w:
        num_eq(c[w], at(c, p)) != 4

at_most_one_clue_per_region(c, n)
region_size_clue(c, n)

for v in corners():
    let deg = num_eq(c.border[edge_of(v)], 1)
    if has_value(o, v):
        if at(o, v) == 2:
            deg == 3
        if at(o, v) == 1:
            deg == 4
    else:
        let near = false
        for d in dirs4:
            if in_grid(v, dr_of(d), dc_of(d)):
                if has_value(o, shift(v, dr_of(d), dc_of(d))):
                    let near = true
        if near:
            deg != 3 and deg != 4
