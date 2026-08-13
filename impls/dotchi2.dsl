# dotchi2 — Dotchi Dotchi Loop
# 每个区域要么走遍白圈不走黑圈，要么走遍黑圈不走白圈；每区至少走一个圈。
# 黑圈转弯，白圈直行。

import "loops"
import "regions"

cloop(e)

for p in clue_cells(o):
    if at(o, p) == 1:
        on_loop(e, p) => goes_straight(e, p)
    if at(o, p) == 2:
        on_loop(e, p) => turns(e, p)

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
