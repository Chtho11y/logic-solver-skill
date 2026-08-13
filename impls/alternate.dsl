# alternate — 交替回路
# 回路经过所有格子。若两个圆圈被回路边直接相连，则颜色不同。
# 未编码：沿回路中间隔着空格的连续同色圆圈。

import "loops"

full_loop(e)

for p in clue_cells(o):
    for q in adj4(p):
        if has_value(o, q):
            if before(p, q):
                link_between(e, p, q) == 1 => at(o, p) != at(o, q)
