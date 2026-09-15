# 回路经过所有圆圈。白圈两臂等长，黑圈两臂不等；数字 = 两臂长度之和。
import "loops"

def balance(e, o, n):
    cloop(e)
    for p in clue_cells(o):
        on_loop(e, p)
        if o[p] == 1:
            two_arms_equal(e, p)
        else:
            not two_arms_equal(e, p)
    for p in clue_cells(n):
        on_loop(e, p)
        two_arm_sum(e, p) == n[p]

balance(e, o, n)
