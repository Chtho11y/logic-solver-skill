# 涂黑一条宽度为一且不和自身接触的蛇；黑圈 = 蛇的一端，白圈 = 蛇身（非端点）；
# 盘面外的数字表示此行或此列内涂黑格的个数。
import "shading"
import "outside"

snake_shape(x, 1)
row_count(x, 1, "left")
col_count(x, 1, "top")

for p in clue_cells(o):
    is_black(x, p)
    if at(o, p) == 2:
        n_adj4(x, p, 1) == 1
    else:
        n_adj4(x, p, 1) == 2
