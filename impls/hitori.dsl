# hitori — 数壹
# 涂黑一些格子，使得涂黑的格子之间不相邻，且留白的格子连通成一个整体。
# 任意两个同行或同列的留白格不能包含相同的数字。

import "shading"

island_rule(x)

for r in rows:
    for p in r:
        for q in r:
            if col_of(p) < col_of(q):
                if at(n, p) == at(n, q):
                    is_black(x, p) or is_black(x, q)

for c in cols:
    for p in c:
        for q in c:
            if row_of(p) < row_of(q):
                if at(n, p) == at(n, q):
                    is_black(x, p) or is_black(x, q)
