# waterwalk — 水面行者
# 回路经过所有数字格。不能连续经过超过两个水格。
# 数字 = 沿回路的连续白格段长度。n=1 已编码；n>1 的沿回路段长未编码。

import "loops2"

cloop(e)

for p in clue_cells(n):
    on_loop(e, p)
    not marked(w, p)

for p in cells():
    if marked(w, p):
        on_loop(e, p) => loop_water_neighbours(e, w, p) <= 1

for p in clue_cells(n):
    if at(n, p) == 1:
        loop_water_neighbours(e, w, p) == 0
