# snail — 蜗牛
# 1..K 每行每列各一次。从圆圈起沿螺旋，填数按 1..K 循环。叉格不填。

import "fill2"

let vals = values_param([1, 2])
let k = vals.size

for p in cells():
    if has_value(m, p):
        at(x, p) == 0
    else:
        allowed_or_empty(x, p, vals)

each_once(x, vals)

let started = 0
let seq = 0
for p in spiral():
    if has_value(o, p):
        let started = 1
    if started == 1:
        let seq = ite(at(x, p) > 0, ite(seq == k, 1, seq + 1), seq)
        at(x, p) > 0 => at(x, p) == seq
