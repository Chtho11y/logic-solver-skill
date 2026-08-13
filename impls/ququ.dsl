# ququ — 区区
# 每一组连通留白格恰好包含一个数字，数字 = 该留白组格数。
# 未编码：对角接触的涂黑连通组不能全等。

import "shading"

clue_cells_white(x, n)
group_size_clue(x, n)
cc_count(x, 0) == clue_cells(n).size
