# ============================================================================
# fill.dsl — templates for the 填写 family (numbers written into cells).
#
#   import "fill"
# ============================================================================

import "core"


def latin(x):
    # 每行每列的数字互不相同
    for r in rows:
        distinct(x[r])
    for c in cols:
        distinct(x[c])

def latin_1_to_n(x):
    # 方阵：每行每列是 1..N 的排列（N = 列数）
    subset_latin(x, cols.size)

def subset_latin(x, k):
    # 每行每列中 1..k 各出现一次，其余格子为 0
    for p in cells():
        at(x, p) >= 0
        at(x, p) <= k
    for line in rows:
        subset_latin_line(x, line, k)
    for line in cols:
        subset_latin_line(x, line, k)

def subset_latin_line(x, line, k):
    let filled = 0
    for p in line:
        let filled = filled + b2i(at(x, p) != 0)
    filled == k
    for p in line:
        for q in line:
            if before(p, q):
                (at(x, p) != 0 and at(x, q) != 0) => at(x, p) != at(x, q)

def boxes(x, w, h):
    # 每个 w×h 宫内的数字互不相同
    for b in grid(w, h):
        distinct(x[b])

def region_1_to_n(x):
    # 每个区域里包含数字 1~N，其中 N 是这个区域的总格数
    for reg in regions:
        distinct(x[reg])
        for p in reg:
            at(x, p) >= 1
            at(x, p) <= reg.size

def touching_differ(x):
    # 接触（含对角）的格子里不能有相同的数字
    for p in cells():
        for q in adj8(p):
            at(x, p) != at(x, q)

def adjacent_differ(x):
    for p in cells():
        for q in adj4(p):
            at(x, p) != at(x, q)

def kropki_white(a, b):
    return abs(a - b) == 1

def kropki_black(a, b):
    return a == b + b or b == a + a

def region_consecutive(x):
    # 每个区域内的所有数必须构成一个连续数字序列（顺序任意）
    for reg in regions:
        distinct(x[reg])
        max(x[reg]) - min(x[reg]) == reg.size - 1


# -- arrows -------------------------------------------------------------------
# An arrow variable holds a direction code 0..3 (UP/DOWN/LEFT/RIGHT).

def arrow_target(a, p, d):
    # The cell one step from `p` in direction `d`, or an empty region.
    if d == UP:
        return shift(p, -1, 0)
    if d == DOWN:
        return shift(p, 1, 0)
    if d == LEFT:
        return shift(p, 0, -1)
    return shift(p, 0, 1)

def arrow_ray(p, d):
    return dir(p, d)

def arrows_never_leave_board(a):
    for p in cells():
        for d in [UP, DOWN, LEFT, RIGHT]:
            if arrow_target(a, p, d).size == 0:
                at(a, p) != d
