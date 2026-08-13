# goishi — 捡棋子
# 棋子按 1..K 顺序捡走；连续两步同行或同列且中间无未捡子；禁止 180° 掉头。

import "fill2"

let k = clue_cells(o).size

for p in cells():
    if has_value(o, p):
        at(x, p) >= 1
        at(x, p) <= k
    else:
        at(x, p) == 0

if k >= 1:
    distinct(x[clue_cells(o)])

for p in clue_cells(o):
    for q in clue_cells(o):
        if before(p, q):
            if row_of(p) == row_of(q) or col_of(p) == col_of(q):
                let blocked = 0
                for r in clue_cells(o):
                    if row_of(p) == row_of(q):
                        if row_of(r) == row_of(p):
                            if (col_of(p) - col_of(r)) * (col_of(q) - col_of(r)) < 0:
                                let blocked = blocked + b2i(at(x, r) > at(x, p) and at(x, p) + 1 == at(x, q))
                                let blocked = blocked + b2i(at(x, r) > at(x, q) and at(x, q) + 1 == at(x, p))
                    if col_of(p) == col_of(q):
                        if col_of(r) == col_of(p):
                            if (row_of(p) - row_of(r)) * (row_of(q) - row_of(r)) < 0:
                                let blocked = blocked + b2i(at(x, r) > at(x, p) and at(x, p) + 1 == at(x, q))
                                let blocked = blocked + b2i(at(x, r) > at(x, q) and at(x, q) + 1 == at(x, p))
                at(x, p) + 1 == at(x, q) => blocked == 0
                at(x, q) + 1 == at(x, p) => blocked == 0
            else:
                at(x, p) + 1 != at(x, q)
                at(x, q) + 1 != at(x, p)

for p in clue_cells(o):
    for q in clue_cells(o):
        for s in clue_cells(o):
            if row_of(p) == row_of(q) and row_of(q) == row_of(s):
                if (col_of(p) - col_of(q)) * (col_of(s) - col_of(q)) < 0:
                    not (at(x, q) == at(x, p) + 1 and at(x, s) == at(x, q) + 1)
            if col_of(p) == col_of(q) and col_of(q) == col_of(s):
                if (row_of(p) - row_of(q)) * (row_of(s) - row_of(q)) < 0:
                    not (at(x, q) == at(x, p) + 1 and at(x, s) == at(x, q) + 1)
