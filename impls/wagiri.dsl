# wagiri — 斜线(环和切)
# 每格一条对角线。顶点数字=引出斜线数。
# 輪/切（格子是否属于环）当前未编码，见 unencodedClues。

import "fill2"

for v in clue_cells(n):
    slash_degree(g, v) == at(n, v)
