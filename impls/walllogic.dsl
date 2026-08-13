# walllogic — 四风
# 从数字格伸出直臂覆盖全部空格；数字 = 四向臂占用格数之和。

import "paths2"

no_outer_links(e)

for p in cells():
    if has_value(n, p):
        wind_len(e, n, p, UP) + wind_len(e, n, p, DOWN) + wind_len(e, n, p, LEFT) + wind_len(e, n, p, RIGHT) == at(n, p)
    else:
        cdeg(e, p) == 1 or cdeg(e, p) == 2
        cdeg(e, p) == 2 => goes_straight(e, p)

for p in cells():
    for q in adj4(p):
        if before(p, q):
            if has_value(n, p) and has_value(n, q):
                link_between(e, p, q) == 0
