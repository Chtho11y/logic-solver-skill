# pentopia — 近视五格
# 放置若干五格骨牌，彼此八邻域不相接。箭头格不被覆盖。
# 箭头指向所有离此格最近的被覆盖格所在的横竖方向。形状目录未编码。

import "shading"
import "place2"

groups_of_size(x, 1, 5)
cc8_count(x, 1) == cc_count(x, 1)

for p in clue_cells(a):
    is_white(x, p)
    myopia_bits(x, p, at(a, p), 1)
