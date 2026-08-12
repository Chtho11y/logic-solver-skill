# mines — 扫雷
# 在一些空格里放一枚地雷；数字表示与此格接触的（至多）八格中的总雷数。

import "core"

for p in clue_cells(n):
    at(x, p) == 0
    num_eq(x[adj8(p)], 1) == at(n, p)
