# lightshadow — 黑白分明
# 每一组连通的涂黑格恰有一个黑数字（且无白数字），每一组连通的涂白格恰有一个
# 白数字（且无黑数字）；数字表示其所在连通组的面积。

import "shading"

let sz = cc_size(x)

for p in clue_cells(bn):
    is_black(x, p)
    at(sz, p) == at(bn, p)

for p in clue_cells(wn):
    is_white(x, p)
    at(sz, p) == at(wn, p)

cc_count(x, 1) == clue_cells(bn).size
cc_count(x, 0) == clue_cells(wn).size
