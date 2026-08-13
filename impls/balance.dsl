# balance — 平衡回路
# 经过所有带圈格。白圈：两条臂等长；黑圈：两条臂不等长。数字 = 两臂长度之和（含圈格）。

import "loops"

cloop(e)

for p in clue_cells(o):
    on_loop(e, p)
    let lu = arm_used_len(e, p, UP)
    let ld = arm_used_len(e, p, DOWN)
    let ll = arm_used_len(e, p, LEFT)
    let lr = arm_used_len(e, p, RIGHT)
    let total = lu + ld + ll + lr
    if at(o, p) == 1:
        for d1, L1 in [[UP, lu], [DOWN, ld], [LEFT, ll], [RIGHT, lr]]:
            for d2, L2 in [[UP, lu], [DOWN, ld], [LEFT, ll], [RIGHT, lr]]:
                if d1 < d2:
                    link_dir(e, p, d1) == 1 and link_dir(e, p, d2) == 1 => L1 == L2
    if at(o, p) == 2:
        for d1, L1 in [[UP, lu], [DOWN, ld], [LEFT, ll], [RIGHT, lr]]:
            for d2, L2 in [[UP, lu], [DOWN, ld], [LEFT, ll], [RIGHT, lr]]:
                if d1 < d2:
                    link_dir(e, p, d1) == 1 and link_dir(e, p, d2) == 1 => L1 != L2
    if has_value(n, p):
        total == at(n, p)
