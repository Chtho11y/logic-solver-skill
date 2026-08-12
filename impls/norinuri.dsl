# 涂黑一些 1x2 的长方形（互不相邻），把盘面分为若干留白区域；数字格不能涂黑；
# 每一组连通的留白格恰好包含一个数字；数字 = 其所在留白连通组的格数。
import "shading"

all_dominoes(x, 1)
clue_cells_white(x, n)
group_size_clue(x, n)
clues_in_distinct_groups(x, n)
cc_count(x, 0) == clue_cells(n).size
