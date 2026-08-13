# swslither — 羊圈数回
# 数回 + 羊在回路内、狼在回路外。o: 1=羊 2=狼。

import "loops"

loop(e)

for p in clue_cells(n):
    cell_edge_count(e, p) == at(n, p)

inside_flag(e, ins)

for p in clue_cells(o):
    if at(o, p) == 1:
        at(ins, p) == 1
    if at(o, p) == 2:
        at(ins, p) == 0
