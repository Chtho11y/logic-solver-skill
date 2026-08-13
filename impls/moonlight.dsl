# moonlight — 星光
# 空格放星(1)或云(2)。行星与 × 不放图形。盘外 left/top = 每行/列星数，right/bottom = 云数。
# 行星照明与象限未编码。

import "core"
import "outside"

for p in clue_cells(o):
    at(x, p) == 0
for p in clue_cells(w):
    at(x, p) == 0

row_count(x, 1, "left")
col_count(x, 1, "top")
row_count(x, 2, "right")
col_count(x, 2, "bottom")
