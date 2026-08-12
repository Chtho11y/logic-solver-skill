# nurikabe — 数墙
# 涂黑一些空格，使得所有涂黑的格子连通成一个整体，且没有全部涂黑的 2x2 结构。
# 每一组连通的留白格必须恰好包含一个数字，数字表示其所在留白连通组的格数。

import "shading"

wall_rule(x)

for p in clue_cells(n):
    is_white(x, p)
    at(cc_size(x), p) == at(n, p)

# 白连通组数 == 数字个数，配合“每个数字在一个白组里”即得双射。
cc_count(x, 0) == clue_cells(n).size
