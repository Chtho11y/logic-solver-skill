# kakuro — 数和
# 白格填 1-9，每段不重复。黑格上 h/v 分别为右方横段 / 下方纵段之和。

import "fill2"

for p in cells():
    if has_value(b, p):
        at(x, p) == 0
    else:
        at(x, p) >= 1
        at(x, p) <= 9

def run_right(p):
    let out = []
    let alive = true
    for q in dir(p, RIGHT):
        if alive:
            if has_value(b, q):
                let alive = false
            else:
                let out = out.append(q)
    return out

def run_down(p):
    let out = []
    let alive = true
    for q in dir(p, DOWN):
        if alive:
            if has_value(b, q):
                let alive = false
            else:
                let out = out.append(q)
    return out

for p in clue_cells(h):
    let seg = run_right(p)
    if seg.size > 0:
        sum(x[seg]) == at(h, p)
        distinct(x[seg])

for p in clue_cells(v):
    let seg = run_down(p)
    if seg.size > 0:
        sum(x[seg]) == at(v, p)
        distinct(x[seg])
