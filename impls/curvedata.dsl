# curvedata — 曲线数据
# 每格都属于某个图形；每个连通图形恰好经过一个提示。
# 提示形状（不可旋转翻转，臂长可伸缩）未编码。

import "paths2"

no_outer_links(e)
linked_same_x(e, x)

for p in cells():
    cdeg(e, p) >= 1
    at(x, p) != 0

for p in clue_cells(o):
    at(x, p) == cell_idx(p) + 1
    cc_count(x, at(x, p)) == 1

for p in cells():
    let ok = false
    for q in clue_cells(o):
        let ok = ok or (at(x, p) == cell_idx(q) + 1)
    ok
