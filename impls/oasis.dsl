# 涂黑格互不相邻、留白连通；无全白 2x2；白圈格必须留白；
# 白圈数字 = 从此格出发只经空白格可以走到的白圈个数。
import "shading"

island_rule(x)
no_white_2x2(x)
clue_cells_white(x, n)
