# mrtile — 复制瓦片
# 数字表示其所在涂黑连通组的面积。每个涂黑连通组必须对角贴上另一组。
# 未编码：对角相邻的那一组还须与本组全等。

import "shading"

clue_cells_black(x, n)
group_size_clue(x, n)

let s4 = cc_size(x)
let s8 = cc8_size(x)
for p in cells():
    is_black(x, p) => at(s8, p) > at(s4, p)
