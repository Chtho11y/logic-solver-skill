# 每个区域内的水体必须稳定：留白格与涂黑格只能纵向相邻且留白格在上（水往下沉），
# 而同一区域内每一组涂黑连通组的水面必须在同一高度（水面是平的）；
# 盘面外的数字表示此行或此列内涂黑格的个数。
import "shading"
import "regions"
import "outside"

for p in cells():
    let below = shift(p, 1, 0)
    if in_grid(p, 1, 0):
        if same_region(p, below):
            # 水往下沉：此格有水则其下方（同区域）也有水。
            is_black(x, p) => is_black(x, below)
    let right = shift(p, 0, 1)
    if in_grid(p, 0, 1):
        if same_region(p, right):
            # 水面是平的：同区域同一行的相邻两格水位相同。
            at(x, p) == at(x, right)

row_count(x, 1, "left")
col_count(x, 1, "top")
