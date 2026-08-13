# tapaloop — 土派回路
# 数字为与此格接触的八格中，回路连续经过的段长。
# 单数提示约束为恰好一段连续；多个提示仅约束总和与段数。

import "loops2"

cloop(e)

for p in clue_cells(n):
    let extra = 0
    if has_value(n2, p):
        let extra = extra + at(n2, p)
    if has_value(n3, p):
        let extra = extra + at(n3, p)
    if has_value(n4, p):
        let extra = extra + at(n4, p)
    let k = 1
    if has_value(n2, p):
        let k = k + 1
    if has_value(n3, p):
        let k = k + 1
    if has_value(n4, p):
        let k = k + 1
    around8_sum(e, p) == at(n, p) + extra
    if k == 1:
        around8_single(e, p, at(n, p))
    else:
        around8_trans(e, p) == 2 * k
