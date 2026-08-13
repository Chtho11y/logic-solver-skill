# anglers — 渔夫
# 每个数字一条路径连到唯一一条鱼；覆盖全部格子。数字 = 路径格数（含鱼格）。

import "paths2"

no_outer_links(e)
linked_same_x(e, x)

for p in cells():
    if has_value(n, p) or has_value(o, p):
        at(x, p) != 0
        cdeg(e, p) == 1
    else:
        at(x, p) != 0
        cdeg(e, p) == 2

for p in clue_cells(n):
    at(x, p) == cell_idx(p) + 1
    cc_count(x, at(x, p)) == 1
    let fishes = 0
    let sz = 0
    for q in cells():
        let sz = sz + b2i(at(x, q) == at(x, p))
        if has_value(o, q):
            let fishes = fishes + b2i(at(x, q) == at(x, p))
    fishes == 1
    sz == at(n, p)

for p in clue_cells(o):
    let nums = 0
    for q in clue_cells(n):
        let nums = nums + b2i(at(x, p) == at(x, q))
    nums == 1
