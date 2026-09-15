# akari — 美术馆
# 在一些空格内放置灯泡照亮所有空格；任意两个灯泡不能互相照亮；
# 黑格里的数字表示与之相邻的（至多）四格中的灯泡个数。

import "core"

def lit_count(x, w, p):
    let total = 0
    for d in [UP, DOWN, LEFT, RIGHT]:
        let alive = true
        for q in dir(p, d):
            if alive:
                if has_value(w, q):
                    let alive = false
                else:
                    let total = total + b2i(x[q] == 1)
    return total

def akari(x, w, n):
    for p in clue_cells(w):
        x[p] == 0

    for p in clue_cells(n):
        num_eq(x[adj4(p)], 1) == n[p]

    for p in cells():
        if not has_value(w, p):
            let seen = lit_count(x, w, p)
            x[p] == 1 or seen >= 1
            x[p] == 1 => seen == 0

akari(x, w, n)
