# railpool — 轨道库
# 经过所有格子。区域内数字是与该区域相交的直线段长度集合（不重复）。

import "loops2"
import "regions"

full_loop(e)

for p in clue_cells(n):
    for q in clue_cells(n):
        if before(p, q):
            if same_region(p, q):
                if at(n, p) > 0 and at(n, q) > 0:
                    at(n, p) != at(n, q)

for p in cells():
    let reg = region_of(p)
    let has = false
    for q in reg:
        if has_value(n, q):
            let has = true
    if has:
        on_loop(e, p) and goes_straight(e, p) => length_in_region(n, reg, full_straight_len(e, p))
        for d in dirs4:
            link_dir(e, p, d) == 1 and turns(e, p) => length_in_region(n, reg, arm_used_len(e, p, d))

for p in clue_cells(n):
    if at(n, p) > 0:
        segment_hits_region(e, region_of(p), at(n, p))
    else:
        region_has_any_segment(e, region_of(p))

def length_in_region(n, reg, L):
    let clues = []
    for q in reg:
        if has_value(n, q):
            let clues = clues.append(q)
    return any_where(clues, fn (q) -> at(n, q) < 0 or L == at(n, q))

def cell_has_segment(e, p):
    let hit = on_loop(e, p) and goes_straight(e, p)
    for d in dirs4:
        let hit = hit or (turns(e, p) and link_dir(e, p, d) == 1)
    return hit

def cell_hits_len(e, p, L):
    let hit = on_loop(e, p) and goes_straight(e, p) and full_straight_len(e, p) == L
    for d in dirs4:
        let hit = hit or (turns(e, p) and link_dir(e, p, d) == 1 and arm_used_len(e, p, d) == L)
    return hit

def region_has_any_segment(e, reg):
    return any_where(reg, fn (p) -> cell_has_segment(e, p))

def segment_hits_region(e, reg, L):
    return any_where(reg, fn (p) -> cell_hits_len(e, p, L))
