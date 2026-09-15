# 每行每列两颗星，星不能接触（含对角）；盘外数字 = 两星之间的空格数。
import "outside"

def gaps(x):
    for r in rows:
        num_eq(x[r], 1) == 2
    for c in cols:
        num_eq(x[c], 1) == 2
    no_touch(x, 1)
    outside_gap_between(x, 1)

gaps(x)
