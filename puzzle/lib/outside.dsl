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
    for j in cols:
        let k = side_clue(side, col_of(j[0]))
        if not no_clue(k):
            num_eq(x[j], v) == k

def row_count(x, v, side):
    for i in rows:
        let k = side_clue(side, row_of(i[0]))
        if not no_clue(k):
            num_eq(x[i], v) == k

def col_runs(x, side):
    # 盘面外的数字依次表示此列中每一段连续涂黑格的长度
    for j in cols:
        let k = side_clue(side, col_of(j[0]))
        if not no_clue(k):
            runs(x[j], k)

def row_runs(x, side):
    for i in rows:
        let k = side_clue(side, row_of(i[0]))
        if not no_clue(k):
            runs(x[i], k)


# -- weighted sums (Kakurasu / Box) ------------------------------------------

def row_index_sum(x, side):
    # 盘面外的数字等于此行中涂黑格所在列号之和（列号从 1 开始）
    for i in rows:
        let k = side_clue(side, row_of(i[0]))
        if not no_clue(k):
            weighted_col_sum(x, i) == k

def weighted_col_sum(x, reg):
    let total = 0
    for p in reg:
        let total = total + b2i(is_black(x, p)) * (col_of(p) + 1)
    return total

def col_index_sum(x, side):
    for j in cols:
        let k = side_clue(side, col_of(j[0]))
        if not no_clue(k):
            weighted_row_sum(x, j) == k

def weighted_row_sum(x, reg):
    let total = 0
    for p in reg:
        let total = total + b2i(is_black(x, p)) * (row_of(p) + 1)
    return total


# -- visibility / first-nonzero (Skyscrapers, Easy as ABC, Gaps, Doppelblock)

def visible_count(x, line, from_low):
    # How many positive values in `line` are strictly taller than everything
    # between them and the near side. `from_low` is compile-time: true reads
    # from the first cell (left / top), false from the last (right / bottom).
    let vis = 0
    for p in line:
        let taller = x[p] > 0
        for q in line:
            if from_low:
                if before(q, p):
                    let taller = taller and (x[p] > x[q])
            else:
                if before(p, q):
                    let taller = taller and (x[p] > x[q])
        let vis = vis + b2i(taller)
    return vis

def first_nonzero_low(x, line):
    let first = 0
    let seen = 0
    for p in line:
        let take = seen == 0 and x[p] > 0
        let first = first + ite(take, x[p], 0)
        let seen = seen + b2i(take)
    return first

def first_nonzero_high(x, line):
    let first = 0
    for p in line:
        let first = ite(x[p] > 0, x[p], first)
    return first

def outside_visible(x):
    for i in rows:
        let k = side_clue("left", row_of(i[0]))
        if not no_clue(k):
            visible_count(x, i, true) == k
        let kr = side_clue("right", row_of(i[0]))
        if not no_clue(kr):
            visible_count(x, i, false) == kr
    for j in cols:
        let k = side_clue("top", col_of(j[0]))
        if not no_clue(k):
            visible_count(x, j, true) == k
        let kb = side_clue("bottom", col_of(j[0]))
        if not no_clue(kb):
            visible_count(x, j, false) == kb

def outside_first_letter(x):
    for i in rows:
        let k = side_clue("left", row_of(i[0]))
        if not no_clue(k):
            first_nonzero_low(x, i) == k
        let kr = side_clue("right", row_of(i[0]))
        if not no_clue(kr):
            first_nonzero_high(x, i) == kr
    for j in cols:
        let k = side_clue("top", col_of(j[0]))
        if not no_clue(k):
            first_nonzero_low(x, j) == k
        let kb = side_clue("bottom", col_of(j[0]))
        if not no_clue(kb):
            first_nonzero_high(x, j) == kb

def between_two_count(x, line, v):
    # How many cells sit strictly between the two cells holding `v`.
    let seen = 0
    let gap = 0
    for p in line:
        let seen = seen + b2i(x[p] == v)
        let gap = gap + b2i(seen == 1 and x[p] != v)
    return gap

def outside_gap_between(x, v):
    for i in rows:
        let k = side_clue("left", row_of(i[0]))
        if not no_clue(k):
            between_two_count(x, i, v) == k
        let kr = side_clue("right", row_of(i[0]))
        if not no_clue(kr):
            between_two_count(x, i, v) == kr
    for j in cols:
        let k = side_clue("top", col_of(j[0]))
        if not no_clue(k):
            between_two_count(x, j, v) == k
        let kb = side_clue("bottom", col_of(j[0]))
        if not no_clue(kb):
            between_two_count(x, j, v) == kb

def between_two_sum(x, line, wall):
    # Sum of values strictly between the two cells holding `wall`.
    let seen = 0
    let total = 0
    for p in line:
        let seen = seen + b2i(x[p] == wall)
        let total = total + ite(seen == 1 and x[p] != wall, x[p], 0)
    return total

def outside_between_sum(x, wall):
    for i in rows:
        let k = side_clue("left", row_of(i[0]))
        if not no_clue(k):
            between_two_sum(x, i, wall) == k
        let kr = side_clue("right", row_of(i[0]))
        if not no_clue(kr):
            between_two_sum(x, i, wall) == kr
    for j in cols:
        let k = side_clue("top", col_of(j[0]))
        if not no_clue(k):
            between_two_sum(x, j, wall) == k
        let kb = side_clue("bottom", col_of(j[0]))
        if not no_clue(kb):
            between_two_sum(x, j, wall) == kb
