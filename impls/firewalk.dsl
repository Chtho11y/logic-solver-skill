# firewalk — 烈焰行者
# 经过所有数字格。经过火格必须转弯；火格允许度 4（两次经过）。
# 数字 = 沿回路连续白格段长。n=1 已编码；n>1 未编码。

import "loops2"

cross_loop(e)

for p in cells():
    if marked(w, p):
        let d = cdeg(e, p)
        d == 0 or d == 2 or d == 4
        d == 2 => turns(e, p)
    else:
        cdeg(e, p) == 0 or cdeg(e, p) == 2

for p in clue_cells(n):
    on_loop(e, p)
    not marked(w, p)
    if at(n, p) == 1:
        loop_water_neighbours(e, w, p) == 0
