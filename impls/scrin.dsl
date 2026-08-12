# 每一组涂色的连通组都是长方形且至多包含一个圆圈；所有圆圈必须在涂色格内；
# 所有长方形对角连通成一个环；圈内数字 = 其所在长方形的面积。
import "shading"

is_rect_group(x, 1)
connected8(x, 1)
clue_cells_black(x, n)
group_size_clue(x, n)
clues_in_distinct_groups(x, n)
