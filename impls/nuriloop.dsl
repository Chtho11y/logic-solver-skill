# nuriloop — 数墙回路
# 回路经过一些空格。未被经过的连通组恰好各含一个数字，数字 = 该组格数。
# y：1 = 不在回路上（辅助）。

import "loops"

cloop(e)

for p in cells():
    at(y, p) == b2i(off_loop(e, p))

for p in clue_cells(n):
    at(y, p) == 1
    at(cc_size(y), p) == at(n, p)

cc_count(y, 1) == clue_cells(n).size
