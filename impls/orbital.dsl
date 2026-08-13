# orbital — 行星轨道
# 若干矩形回路，可交叉不可共边/共角。白圈必须在回路上，黑圈必须在恰好一个回路内部。
# 黑圈数字 = 该回路经过的白圈个数。

import "loops2"

rectangular_loops(e)

for p in clue_cells(o):
    if at(o, p) == 1:
        on_drawn_rect(e, p)
    if at(o, p) == 2:
        not on_drawn_rect(e, p)
        inside_drawn_count(e, p) == 1

for p in clue_cells(n):
    let total = 0
    for a in cells():
        for b in cells():
            if row_of(a) < row_of(b):
                if col_of(a) < col_of(b):
                    if in_rect_strict(row_of(a), col_of(a), row_of(b), col_of(b), p):
                        let whites = 0
                        for q in clue_cells(o):
                            if at(o, q) == 1:
                                if on_rect_perim(row_of(a), col_of(a), row_of(b), col_of(b), q):
                                    let whites = whites + 1
                        let total = total + ite(rect_perimeter_ok(e, row_of(a), col_of(a), row_of(b), col_of(b)), whites, 0)
    total == at(n, p)
