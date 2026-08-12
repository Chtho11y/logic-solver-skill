# 涂黑一条宽度为一的蛇；黑圈表示此格是蛇的一端；
# 数字 = 其所在的留白连通组格数。
import "shading"

snake_shape(x, 1)
group_size_clue(x, n)

# 黑圈是蛇的端点。
for p in clue_cells(o):
    is_black(x, p)
    n_adj4(x, p, 1) == 1
