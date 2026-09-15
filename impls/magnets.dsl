# 每个 1x2 区域空着，或放一正一负；相邻同号禁止；盘外为 +/- 个数。
import "outside"
import "regions"

def magnets(x):
    for reg in regions:
        let plus = num_eq(x[reg], 1)
        let minus = num_eq(x[reg], 2)
        (plus == 0 and minus == 0) or (plus == 1 and minus == 1)

    for p in cells():
        for q in adj4(p):
            not (x[p] != 0 and x[p] == x[q])

    row_count(x, 1, "left")
    row_count(x, 2, "right")
    col_count(x, 1, "top")
    col_count(x, 2, "bottom")

magnets(x)
