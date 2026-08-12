# 涂黑格互不相邻、留白连通；每个圆圈恰和一个涂黑格接触；
# 同一行或同一列的三个连续黑格不能等距排列。
import "shading"

island_rule(x)

for p in clue_cells(o):
    n_adj8(x, p, 1) == 1

no_equally_spaced_triple(x)

def no_equally_spaced_triple(x):
    for p in cells():
        for d in [1, 2, 3, 4, 5, 6, 7]:
            forbid_triple(x, p, shift(p, 0, d), shift(p, 0, 2 * d))
            forbid_triple(x, p, shift(p, d, 0), shift(p, 2 * d, 0))

def forbid_triple(x, p, q, r):
    if q.size == 1:
        if r.size == 1:
            not (is_black(x, p) and is_black(x, q) and is_black(x, r))
