# 无三连黑/白；每行每列恰一半涂黑；行互异、列互异；白圈留白、黑圈涂黑。
import "shading"

no_run(x, 1, 3)
no_run(x, 0, 3)
for r in rows:
    num_eq(x[r], 1) == cols.size / 2
for c in cols:
    num_eq(x[c], 1) == rows.size / 2
distinct_rows(x)
distinct_cols(x)

for p in clue_cells(o):
    if at(o, p) == 1:
        at(x, p) == 0
    else:
        at(x, p) == 1
