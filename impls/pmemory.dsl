# pmemory — 记忆的永恒
# 蛇形路径连接两黑圈；宽为 1 且不与自身接触。经过每个灰区至少一次。
# 同形同向灰区内部连线方式相同。

import "paths2"
import "regions"

no_outer_links(e)
connect_links(e)

let ncirc = clue_cells(o).size

for p in cells():
    if has_value(o, p):
        cdeg(e, p) == 1
        at(x, p) >= 1
    else:
        (cdeg(e, p) == 0 and at(x, p) == 0) or (cdeg(e, p) == 2 and at(x, p) >= 1)

let L = 0
for p in cells():
    let L = L + b2i(cdeg(e, p) > 0)

if ncirc == 2:
    let a = clue_cells(o)[0]
    let b = clue_cells(o)[1]
    (at(x, a) == 1 and at(x, b) == L) or (at(x, b) == 1 and at(x, a) == L)
else:
    ncirc == 2

for p in cells():
    for q in adj4(p):
        if before(p, q):
            (cdeg(e, p) > 0 and cdeg(e, q) > 0) == (link_between(e, p, q) == 1)
            link_between(e, p, q) == 1 => abs(at(x, p) - at(x, q)) == 1

for p in cells():
    for q in diag4(p):
        if before(p, q):
            cdeg(e, p) > 0 and cdeg(e, q) > 0 => abs(at(x, p) - at(x, q)) == 2

for reg in regions:
    let ng = 0
    for p in reg:
        if has_value(g, p):
            let ng = ng + 1
    if ng > 0:
        let vis = 0
        for p in reg:
            let vis = vis + b2i(cdeg(e, p) > 0)
        vis >= 1

for a in regions:
    for b in regions:
        if region_id(a[0]) < region_id(b[0]):
            if same_shape(a, b):
                match_links(e, a, b)

def same_shape(a, b):
    if a.size != b.size:
        return false
    let minra = row_of(a[0])
    let minca = col_of(a[0])
    let minrb = row_of(b[0])
    let mincb = col_of(b[0])
    for p in a:
        if row_of(p) < minra:
            let minra = row_of(p)
        if col_of(p) < minca:
            let minca = col_of(p)
    for p in b:
        if row_of(p) < minrb:
            let minrb = row_of(p)
        if col_of(p) < mincb:
            let mincb = col_of(p)
    let ok = true
    for p in a:
        let found = false
        for q in b:
            if row_of(p) - minra == row_of(q) - minrb and col_of(p) - minca == col_of(q) - mincb:
                let found = true
        let ok = ok and found
    return ok

def match_links(e, a, b):
    let minra = row_of(a[0])
    let minca = col_of(a[0])
    let minrb = row_of(b[0])
    let mincb = col_of(b[0])
    for p in a:
        if row_of(p) < minra:
            let minra = row_of(p)
        if col_of(p) < minca:
            let minca = col_of(p)
    for p in b:
        if row_of(p) < minrb:
            let minrb = row_of(p)
        if col_of(p) < mincb:
            let mincb = col_of(p)
    for p in a:
        for q in b:
            if row_of(p) - minra == row_of(q) - minrb and col_of(p) - minca == col_of(q) - mincb:
                link_up(e, p) == link_up(e, q)
                link_down(e, p) == link_down(e, q)
                link_left(e, p) == link_left(e, q)
                link_right(e, p) == link_right(e, q)
