# sashigane — 曲尺分割
# 宽为一的 L 形：恰两个端点、恰一个转弯。圆圈在转弯处；箭头在一端并指向转弯；数字=面积。

import "regions"

for p in cells():
    region_deg(c, p) <= 2
    region_end_count(c, p) == 2
    let bends = 0
    for q in cells():
        let corner = (same_reg_dir(c, q, UP) or same_reg_dir(c, q, DOWN)) and (same_reg_dir(c, q, LEFT) or same_reg_dir(c, q, RIGHT))
        let bends = bends + b2i(at(c, q) == at(c, p) and corner)
    bends == 1

for p in clue_cells(o):
    (same_reg_dir(c, p, UP) or same_reg_dir(c, p, DOWN)) and (same_reg_dir(c, p, LEFT) or same_reg_dir(c, p, RIGHT))

for p in clue_cells(d):
    region_deg(c, p) == 1
    same_reg_dir(c, p, at(d, p))

region_size_clue(c, n)
