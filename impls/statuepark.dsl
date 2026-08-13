# statuepark — 雕像公园
# 放置五格骨牌：互不正交相邻（对角可以），留白连通。
# 黑圈必须被覆盖，白圈不能被覆盖。给出的具体形状目录未编码（任意五格骨牌）。

import "shading"
import "place2"

white_connected(x)
groups_of_size(x, 1, 5)

for p in clue_cells(o):
    if at(o, p) == 2:
        is_black(x, p)
    if at(o, p) == 1:
        is_white(x, p)
