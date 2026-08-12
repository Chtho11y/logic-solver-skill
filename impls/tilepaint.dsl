# tilepaint — 数瓦
# 每个区域要么全部涂黑要么全部留白；盘面外的数字表示此行或此列内涂黑格的个数。

import "shading"
import "regions"
import "outside"

region_uniform(x)
col_count(x, 1, "top")
row_count(x, 1, "left")
