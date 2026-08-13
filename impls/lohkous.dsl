# lohkous — 长宽度量
# 每区恰一提示格。格内数字是该区每一横段、纵段长度的集合（不重复）。

import "place2"

one_clue_per_region(c, n1)

for p in clue_cells(n1):
    if has_value(n1, p):
        region_has_run(c, p, at(n1, p))
    if has_value(n2, p):
        region_has_run(c, p, at(n2, p))
    if has_value(n3, p):
        region_has_run(c, p, at(n3, p))
    every_run_in_clues(c, p, n1, n2, n3)
