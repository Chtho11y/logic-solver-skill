# kissing — Kissing Polyominoes
# 形状仅在被标记的边界上正交相邻。× 格不能被覆盖。形状目录未编码。

import "place2"

for p in cells():
    for q in adj4(p):
        if before(p, q):
            at(c, p) == at(c, q) => at(x, p) == at(x, q)

for p in clue_cells(w):
    at(x, p) == 0

for e in edges():
    let sides = cell_of(e)
    if sides.size == 2:
        for p in sides:
            for q in sides:
                if before(p, q):
                    if has_value(k, e):
                        at(x, p) == 1 and at(x, q) == 1 and at(c, p) != at(c, q)
                    else:
                        (at(x, p) == 1 and at(x, q) == 1) => at(c, p) == at(c, q)
