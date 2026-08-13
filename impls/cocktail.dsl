# cocktail — 鸡尾酒灯
# 每个区域内至多一组连通涂黑格；不同区域的涂黑组不相邻。
# 数字表示区域内涂黑格的个数。所有涂黑格对角连通。不能有全黑 2×2。

import "shading"
import "regions"

at_most_one_black_group_per_region(x)
region_black_count(x, n)
connected8(x, 1)
no_black_2x2(x)
