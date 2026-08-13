# 每组连通的黑格都是长和宽都至少为二的长方形（云团），云团之间不能接触；
# 盘面外的数字表示此行或此列内涂黑格的个数。
import "shading"
import "outside"

is_rect_group(x, 1)
row_count(x, 1, "left")
col_count(x, 1, "top")

for p in cells():
    is_black(x, p) => n_adj4(x, p, 1) >= 2

let ids = cc_id(x)
for p in cells():
    for q in diag4(p):
        is_black(x, p) and is_black(x, q) => at(ids, p) == at(ids, q)
