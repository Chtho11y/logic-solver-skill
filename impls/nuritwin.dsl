# 每个区域内涂黑恰好两组连通格，两组面积相等且互不相邻；
# 所有涂黑格连通；无全黑 2x2；数字 = 其所在区域内一个涂黑连通组的面积。
import "shading"

wall_rule(x)

# 两组等面积 ⟹ 区域内涂黑格数为偶数且至少为 2。
for reg in regions:
    num_eq(x[reg], 1) >= 2
    num_eq(x[reg], 1) % 2 == 0

# 数字是「一组」的面积，故区域总涂黑数为其两倍。
for p in clue_cells(n):
    num_eq(x[region_of(p)], 1) == 2 * at(n, p)
