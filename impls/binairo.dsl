# binairo — 横竖无三
# 无全黑/全白的 1×3 或 3×1；每行每列恰一半涂黑；任意两行、两列图案不同。
# 黑圈必须涂黑，白圈必须留白。

import "shading"

no_run(x, 1, 3)
no_run(x, 0, 3)
half_filled_lines(x)
lines_all_unique(x)

for p in clue_cells(o):
    if at(o, p) == 2:
        is_black(x, p)
    if at(o, p) == 1:
        is_white(x, p)
