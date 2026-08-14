# ubahn — 地铁
# 格心连线连通，无死胡同（度不为 1）。黑格无线。
# 盘外四元组 [交叉, 丁字, 直行, 转弯] 计数（不区分方向）。

import "loops"
import "outside"

for p in cells():
    if has_value(b, p):
        cdeg(e, p) == 0
    else:
        cdeg(e, p) != 1

let used = 0
for ed in edges():
    let used = used + at(e, ed)
connect_links(e) or used == 0

for axis in [0, 1]:
    let side = side_of(axis, 0)
    for ln in lines(axis):
        let k = side_clue(side, ite(axis == 0, row_of(ln[0]), col_of(ln[0])))
        if not no_clue(k):
            if is_list(k):
                if k.size >= 1:
                    let cross = count_where(ln, fn (p) -> cdeg(e, p) == 4)
                    let tee = count_where(ln, fn (p) -> cdeg(e, p) == 3)
                    let straight = count_where(ln, fn (p) -> cdeg(e, p) == 2 and goes_straight(e, p))
                    let turn = count_where(ln, fn (p) -> cdeg(e, p) == 2 and turns(e, p))
                    if k.size >= 1:
                        cross == k[0]
                    if k.size >= 2:
                        tee == k[1]
                    if k.size >= 3:
                        straight == k[2]
                    if k.size >= 4:
                        turn == k[3]
