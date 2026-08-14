# ============================================================================
# outside.dsl — clues written outside the board.
#
#   import "outside"
#
# Outside clues live in the instance parameters, one list per side:
#   param("top")[c]    param("bottom")[c]
#   param("left")[r]   param("right")[r]
# Each entry is either a number, or a list of numbers for “依次表示每一段的
# 长度” style clues. A negative value or a missing entry means “no clue here”.
# ============================================================================

import "core"


def side_clue(side, i):
    # The clue at index i of a side list; -1 (no clue) when absent or short.
    if not has_param(side):
        return 0 - 1
    let clues = param(side)
    if not is_list(clues):
        return 0 - 1
    if i >= clues.size:
        return 0 - 1
    return clues[i]

def no_clue(k):
    # A clue slot counts as empty when it is a negative number.
    if is_list(k):
        return k.size == 0
    return k < 0

def col_count(x, v, side):
    # 盘面外的数字表示此列中 holding `v` 的格数
    line_count(x, v, 1, side)

def row_count(x, v, side):
    line_count(x, v, 0, side)

def line_count(x, v, axis, side):
    for ln in lines(axis):
        let k = side_clue(side, ite(axis == 0, row_of(ln[0]), col_of(ln[0])))
        if not no_clue(k):
            num_eq(x[ln], v) == k

def col_runs(x, side):
    # 盘面外的数字依次表示此列中每一段连续涂黑格的长度
    line_runs(x, 1, side)

def row_runs(x, side):
    line_runs(x, 0, side)

def line_runs(x, axis, side):
    for ln in lines(axis):
        let k = side_clue(side, ite(axis == 0, row_of(ln[0]), col_of(ln[0])))
        if not no_clue(k):
            runs(x[ln], k)

def col_runs_set(x, side):
    # 盘面外的数字表示此列中连续涂黑段长的无序多重集
    line_runs_set(x, 1, side)

def row_runs_set(x, side):
    line_runs_set(x, 0, side)

def line_runs_set(x, axis, side):
    for ln in lines(axis):
        let k = side_clue(side, ite(axis == 0, row_of(ln[0]), col_of(ln[0])))
        if not no_clue(k):
            runs_set(x[ln], k)


# -- weighted sums (Kakurasu / Box) ------------------------------------------

def row_index_sum(x, side):
    # 盘面外的数字等于此行中涂黑格所在列号之和（列号从 1 开始）
    for i in rows:
        let k = side_clue(side, row_of(i[0]))
        if not no_clue(k):
            weighted_col_sum(x, i) == k

def weighted_col_sum(x, reg):
    return sum_where(reg, fn (p) -> is_black(x, p), fn (p) -> col_of(p) + 1)

def col_index_sum(x, side):
    for j in cols:
        let k = side_clue(side, col_of(j[0]))
        if not no_clue(k):
            weighted_row_sum(x, j) == k

def weighted_row_sum(x, reg):
    return sum_where(reg, fn (p) -> is_black(x, p), fn (p) -> row_of(p) + 1)
