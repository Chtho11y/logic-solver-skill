# simplegako — 简单计数
# 每格数字等于该数字在其所在行和列中出现的总次数（含自身）。

import "fill2"

for p in cells():
    at(x, p) >= 1
    at(x, p) == num_eq(x[row(row_of(p))], at(x, p)) + num_eq(x[col(col_of(p))], at(x, p)) - 1
