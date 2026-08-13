# railpool — 轨道库
# 经过所有格子。区域内数字是与该区域相交的直线段长度集合（不重复）。

import "loops2"
import "regions"

full_loop(e)

for p in clue_cells(n):
    for q in clue_cells(n):
        if before(p, q):
            if same_region(p, q):
                at(n, p) != at(n, q)

for p in cells():
    let reg = region_of(p)
    let has = false
    for q in reg:
        if has_value(n, q):
            let has = true
    if has:
        on_loop(e, p) and goes_straight(e, p) => length_in_region(n, reg, full_straight_len(e, p))
        link_up(e, p) == 1 and turns(e, p) => length_in_region(n, reg, arm_used_len(e, p, UP))
        link_down(e, p) == 1 and turns(e, p) => length_in_region(n, reg, arm_used_len(e, p, DOWN))
        link_left(e, p) == 1 and turns(e, p) => length_in_region(n, reg, arm_used_len(e, p, LEFT))
        link_right(e, p) == 1 and turns(e, p) => length_in_region(n, reg, arm_used_len(e, p, RIGHT))

for p in clue_cells(n):
    segment_hits_region(e, region_of(p), at(n, p))

def length_in_region(n, reg, L):
    let ok = false
    for q in reg:
        if has_value(n, q):
            let ok = ok or (L == at(n, q))
    return ok

def segment_hits_region(e, reg, L):
    let hit = false
    for p in reg:
        let hit = hit or (on_loop(e, p) and goes_straight(e, p) and full_straight_len(e, p) == L)
        let hit = hit or (turns(e, p) and link_up(e, p) == 1 and arm_used_len(e, p, UP) == L)
        let hit = hit or (turns(e, p) and link_down(e, p) == 1 and arm_used_len(e, p, DOWN) == L)
        let hit = hit or (turns(e, p) and link_left(e, p) == 1 and arm_used_len(e, p, LEFT) == L)
        let hit = hit or (turns(e, p) and link_right(e, p) == 1 and arm_used_len(e, p, RIGHT) == L)
    return hit
