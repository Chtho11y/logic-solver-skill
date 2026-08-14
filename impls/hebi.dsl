# hebi — 群蛇乱舞
# 蛇为 1-5 路径；蛇与蛇正交不相邻。箭头数字=该方向直到墙/边界的第一个数。

import "fill2"

for p in cells():
    if has_value(b, p):
        at(x, p) == 0
    else:
        at(x, p) >= 0
        at(x, p) <= 5

for p in cells():
    (at(f, p) == 1) == (at(x, p) > 0)

let snakes = cc_count(f, 1)
num_eq(x, 1) == snakes
num_eq(x, 2) == snakes
num_eq(x, 3) == snakes
num_eq(x, 4) == snakes
num_eq(x, 5) == snakes

for p in cells():
    at(f, p) == 1 => at(cc_size(f), p) == 5

for p in cells():
    for q in adj4(p):
        at(f, p) == 1 and at(f, q) == 1 => abs(at(x, p) - at(x, q)) == 1

for p in cells():
    at(x, p) == 1 => num_eq(f[adj4(p)], 1) == 1
    at(x, p) == 5 => num_eq(f[adj4(p)], 1) == 1
    at(x, p) >= 2 and at(x, p) <= 4 => num_eq(f[adj4(p)], 1) == 2

for p in clue_cells(n):
    if has_value(d, p):
        let acc = 0
        let used = 0
        for q in dir(p, at(d, p)):
            if has_value(b, q):
                let used = 1
            else:
                let acc = acc + ite(used == 0, ite(at(x, q) > 0, at(x, q), 0), 0)
                let used = used + b2i(at(x, q) > 0)
        acc == at(n, p)

for p in cells():
    for d in [UP, DOWN, LEFT, RIGHT]:
        let q = step(p, d)
        if in_grid(p, dr_of(d), dc_of(d)):
            let extra = 0
            let alive = true
            for s in dir(q, d):
                if has_value(b, s):
                    let alive = false
                else:
                    let extra = extra + b2i(alive and at(x, s) > 0)
            at(x, p) == 2 and at(x, q) == 1 => extra == 0
