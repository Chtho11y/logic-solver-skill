# tren — 停车场
# 1×2 / 1×3 长方形车，每车恰一数字，每个数字在车上。
# 数字 = 该车沿长边方向可前后滑动的空格总数。

import "place2"

for p in cells():
    let sz = at(c.size, p)
    sz == 1 or sz == 2 or sz == 3
    if sz >= 2:
        region_notch_count(c, p) == 0
        region_height(c, p) == 1 or region_width(c, p) == 1

for p in cells():
    at(c.size, p) >= 2 => num_eq_cells_with_clue(c, n, p) == 1

for p in clue_cells(n):
    at(c.size, p) >= 2
    let h = region_height(c, p)
    let w = region_width(c, p)
    let minc = col_of(p)
    let maxc = col_of(p)
    let minr = row_of(p)
    let maxr = row_of(p)
    for q in cells():
        let here = at(c, q) == at(c, p)
        let minc = ite(here and col_of(q) < minc, col_of(q), minc)
        let maxc = ite(here and col_of(q) > maxc, col_of(q), maxc)
        let minr = ite(here and row_of(q) < minr, row_of(q), minr)
        let maxr = ite(here and row_of(q) > maxr, row_of(q), maxr)
    let left = 0
    let right = 0
    let up = 0
    let down = 0
    for q in cells():
        let on_left = row_of(q) == row_of(p) and col_of(q) < minc
        let gap_l = true
        for u in cells():
            let bet = row_of(u) == row_of(p) and col_of(u) >= col_of(q) and col_of(u) < minc
            let gap_l = gap_l and (not bet or at(c.size, u) == 1)
        let left = left + b2i(on_left and gap_l)
        let on_right = row_of(q) == row_of(p) and col_of(q) > maxc
        let gap_r = true
        for u in cells():
            let bet = row_of(u) == row_of(p) and col_of(u) <= col_of(q) and col_of(u) > maxc
            let gap_r = gap_r and (not bet or at(c.size, u) == 1)
        let right = right + b2i(on_right and gap_r)
        let on_up = col_of(q) == col_of(p) and row_of(q) < minr
        let gap_u = true
        for u in cells():
            let bet = col_of(u) == col_of(p) and row_of(u) >= row_of(q) and row_of(u) < minr
            let gap_u = gap_u and (not bet or at(c.size, u) == 1)
        let up = up + b2i(on_up and gap_u)
        let on_down = col_of(q) == col_of(p) and row_of(q) > maxr
        let gap_d = true
        for u in cells():
            let bet = col_of(u) == col_of(p) and row_of(u) <= row_of(q) and row_of(u) > maxr
            let gap_d = gap_d and (not bet or at(c.size, u) == 1)
        let down = down + b2i(on_down and gap_d)
    if h == 1:
        left + right == at(n, p)
    if w == 1:
        up + down == at(n, p)
