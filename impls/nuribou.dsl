# 每一组连通的留白格恰好包含一个数字；数字 = 其所在留白连通组的格数；
# 每一组连通的涂黑格必须是长或宽为一的长方形，且互相接触的两组涂黑格面积不能相同。
import "shading"

width_one(x, 1)
no2x2(x, 1)
group_size_clue(x, n)
clues_in_distinct_groups(x, n)
cc_count(x, 0) == clue_cells(n).size
