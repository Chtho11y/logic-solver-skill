# aho — 逢三变傻
# 每区恰好一个提示，数字=面积。面积是 3 的倍数则为 L 形（外接矩形去一角小矩形），
# 否则为长方形。L 形判据：连通 + 恰好一个 2x2 缺一角。

import "regions"

one_clue_per_region(c, n)
region_size_clue(c, n)

for p in cells():
    let notches = region_notch_count(c, p)
    if at(c.size, p) % 3 == 0:
        notches == 1
    else:
        notches == 0
