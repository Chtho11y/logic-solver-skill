# aqre — 黑白无四
# 所有涂黑的格子连通；没有全黑或全白的 1x4 / 4x1 结构；数字表示此区域内涂黑格数。

import "shading"

black_connected(x)

for w in slide(4, 1):
    num_eq(x[w], 1) != 4
    num_eq(x[w], 0) != 4
for w in slide(1, 4):
    num_eq(x[w], 1) != 4
    num_eq(x[w], 0) != 4

region_black_count(x, n)
