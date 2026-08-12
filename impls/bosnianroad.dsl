# 涂黑格连通成一个不和自身接触的环；数字格不能涂黑；
# 数字 = 与此格接触的（至多）八格中的涂黑格个数。
import "shading"

cycle_shape(x, 1)
clue_cells_white(x, n)
adj8_black_clue(x, n)
