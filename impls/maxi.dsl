# maxi — 极大回路
# 经过所有格子。数字 = 单次经过该区域的最长连续段。
# 编码为访问次数与最长段的鸽笼不等式（最大值“必须达到”未强制到格）。

import "loops2"
import "regions"

full_loop(e)

for p in clue_cells(n):
    let reg = region_of(p)
    let xings = region_crossings(e, reg)
    let L = at(n, p)
    xings == 0 => L == reg.size
    xings != 0 => xings * L >= 2 * reg.size
    xings != 0 => 2 * L <= 2 * reg.size - xings + 2
