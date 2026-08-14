# dosufuwa — 气球铅球
# 每区域一个气球（1）和一个铅球（2）。
# 铅球在盘底、黑格之上或另一铅球之上；气球在盘顶、黑格之下或另一气球之下。

import "core"
import "regions"

for p in cells():
    if has_value(w, p):
        at(x, p) == 0

for reg in regions:
    num_eq(x[reg], 1) == 1
    num_eq(x[reg], 2) == 1

for p in cells():
    let down = shift(p, 1, 0)
    if in_grid(p, 1, 0):
        at(x, p) == 2 => has_value(w, down) or at(x, down) == 2
    let up = shift(p, -1, 0)
    if in_grid(p, -1, 0):
        at(x, p) == 1 => has_value(w, up) or at(x, up) == 1
