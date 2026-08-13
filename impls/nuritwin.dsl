# 每个区域内涂黑恰好两组连通格，两组面积相等且互不相邻；
# 所有涂黑格连通；无全黑 2x2；数字 = 其所在区域内一个涂黑连通组的面积。
import "shading"

wall_rule(x)

for reg in regions:
    cc_count_in(x, 1, reg) == 2
    cc8_count_in(x, 1, reg) == 2
    let nb = num_eq(x[reg], 1)
    for p in reg:
        is_black(x, p) => cc_size_in(x, p, reg) * 2 == nb

for p in clue_cells(n):
    num_eq(x[region_of(p)], 1) == 2 * at(n, p)
