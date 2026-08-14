# lits — 四格骨墙
# 每个区域内涂黑一个四格骨牌；所有涂黑格连通；无全黑 2x2；
# 不同区域中全等的四格骨牌不能相邻。
#
# 形状编号 t: 0=I 1=L/J 2=S/Z 3=T。判据（在无 2x2 全黑的前提下）：
#   * 区域内存在黑格的“同区域黑邻居数”为 3          -> T
#   * 否则按 “恰含该区域 3 个黑格的 2x2 窗口数” 判断：0 -> I, 1 -> L, 2 -> S

import "shading"
import "regions"

black_connected(x)
no_black_2x2(x)

for reg in regions:
    num_eq(x[reg], 1) == 4
    # 4 个黑格连通 <=> 区域内有序黑相邻对数 >= 6
    ordered_pairs_in(x, reg, 1) >= 6

    let rid = region_id(reg[0])
    let ty = at(t, reg[0])
    for p in reg:
        at(t, p) == ty

    let deg3 = any_where(reg, fn (p) -> is_black(x, p) and in_region_count(x, p, 1) == 3)

    let c3 = 0
    for w in slide(2, 2):
        let sub = region_cells_in(w, rid)
        if sub.size >= 3:
            let c3 = c3 + b2i(num_eq(x[sub], 1) == 3)

    (ty == 3) == deg3
    (ty == 0) == (not deg3 and c3 == 0)
    (ty == 1) == (not deg3 and c3 == 1)
    (ty == 2) == (not deg3 and c3 == 2)

for p in cells():
    for q in adj4(p):
        if not same_region(p, q):
            is_black(x, p) and is_black(x, q) => at(t, p) != at(t, q)
