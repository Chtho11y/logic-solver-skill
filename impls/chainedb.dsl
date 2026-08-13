# chainedb — 区块链
# 每个涂黑连通组恰好包含一个数字，数字 = 该组面积（问号 n<0 不限制大小）。
# 每个涂黑组必须对角贴上另一组（从而属于某条链）。
# 未编码：同一条链里的两个涂黑组不能全等。

import "shading"

clue_cells_black(x, n)
cc_count(x, 1) == clue_cells(n).size

let sz = cc_size(x)
for p in clue_cells(n):
    if at(n, p) >= 0:
        at(sz, p) == at(n, p)

let s4 = cc_size(x)
let s8 = cc8_size(x)
for p in cells():
    is_black(x, p) => at(s8, p) > at(s4, p)
