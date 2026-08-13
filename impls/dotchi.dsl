# dotchi — 二择回路
# 经过所有白圈、不经过黑圈。每个区域内：要么所有白圈格直行，要么所有白圈格转弯。

import "loops"
import "regions"

cloop(e)

for p in clue_cells(o):
    if at(o, p) == 1:
        on_loop(e, p)
    if at(o, p) == 2:
        off_loop(e, p)

for p in clue_cells(o):
    for q in clue_cells(o):
        if before(p, q):
            if same_region(p, q):
                if at(o, p) == 1 and at(o, q) == 1:
                    turns(e, p) == turns(e, q)
