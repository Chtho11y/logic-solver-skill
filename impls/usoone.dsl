# 涂黑格互不相邻、留白连通；数字 = 相邻四格中涂黑格数；数字格不能涂黑；
# 每个区域内恰好有一个错误的数字。
import "shading"

island_rule(x)
clue_cells_white(x, n)

for reg in regions:
    wrong_clues_in(x, n, reg) == 1

def wrong_clues_in(x, n, reg):
    let clues = []
    for p in reg:
        if has_value(n, p):
            let clues = clues.append(p)
    return count_where(clues, fn (p) -> n_adj4(x, p, 1) != at(n, p))
