# ringring — 环环相扣
# 用矩形回路覆盖每个空格。可交叉，不可共边/共角。黑格不经过。

import "loops2"

rectangular_loops(e)

for p in cells():
    if marked(w, p):
        off_loop(e, p)
        not on_drawn_rect(e, p)
    else:
        on_drawn_rect(e, p)
