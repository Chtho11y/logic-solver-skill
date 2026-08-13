# moonsun — 日月交替
# 回路恰好经过每个区域一次，且每区至少经过一个符号。
# 每区要么走遍太阳不走月亮，要么走遍月亮不走太阳，相邻经过的区域必须切换。

import "loops"
import "regions"

cloop(e)

for reg in regions:
    region_crossings(e, reg) == 2

for p in clue_cells(o):
    for q in clue_cells(o):
        if same_region(p, q):
            on_loop(e, p) and at(o, p) == at(o, q) => on_loop(e, q)
            on_loop(e, p) and at(o, p) != at(o, q) => off_loop(e, q)

for p in cells():
    let n = 0
    for q in region_of(p):
        if has_value(o, q):
            let n = n + b2i(on_loop(e, q))
    n >= 1

for p in cells():
    for q in adj4(p):
        if before(p, q):
            if not same_region(p, q):
                link_between(e, p, q) == 1 => takes_sun(e, o, p) != takes_sun(e, o, q)

def takes_sun(e, o, p):
    let hit = false
    for q in region_of(p):
        if has_value(o, q):
            if at(o, q) == 1:
                let hit = hit or on_loop(e, q)
    return hit
