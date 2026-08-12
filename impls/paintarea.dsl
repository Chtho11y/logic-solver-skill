# paintarea — 涂鸦区域
# 所有涂黑格连通、无全黑或全白 2x2；每个区域要么全黑要么全白；
# 数字表示与之相邻的（至多）四格中涂黑格的个数。

import "shading"
import "regions"

black_connected(x)
no_mono_2x2(x)
region_uniform(x)
adj_black_clue(x, n)
