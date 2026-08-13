# stostone — 垒石
# 每个区域恰好一组连通涂黑格，不同区域的涂黑组不相邻。
# 数字表示区域内涂黑格的个数。各组保持形状垂直下落后，恰好覆盖盘面下半部分。

import "shading"
import "regions"

one_black_group_per_region(x)
region_black_count(x, n)
drop_covers(x, rows.size / 2)
