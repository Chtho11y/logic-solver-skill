# simpleloop — 简单回路
# 画一条经过所有空格中心且不自交的回路（黑格不经过）。

import "loops"

cloop(e)

for p in cells():
    if has_value(w, p):
        off_loop(e, p)
    else:
        on_loop(e, p)
