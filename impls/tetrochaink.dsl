# 每个涂黑连通组均为四格骨牌；所有骨牌对角连通；
# 盘面内的点提示其所接触的（至多）四格中涂黑格和留白格哪种更多。
import "shading"

groups_of_size(x, 1, 4)
connected8(x, 1)
majority_dot_clue(x, t)
