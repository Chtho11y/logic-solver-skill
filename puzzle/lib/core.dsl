# ============================================================================
# core.dsl — building blocks shared by every puzzle family.
#
#   import "core"
#
# Conventions used throughout the library:
#   * a *shading* variable is an integer cell variable with domain 0..1,
#     where 1 = 涂黑 (black/filled) and 0 = 留白 (white/empty);
#   * `at(x, p)` unwraps a variable at a single point into a plain scalar —
#     always use it instead of `x[p]` when you need a scalar, because `x[p]`
#     yields a one-element list and `and` merges lists instead of conjoining.
# ============================================================================


# -- predicates over a single cell -------------------------------------------

def eq(x, p, v):
    return at(x, p) == v

def is_black(x, p):
    return at(x, p) == 1

def is_white(x, p):
    return at(x, p) == 0


# -- neighbourhood counting ---------------------------------------------------

def n_adj4(x, p, v):
    # How many of the (at most) 4 orthogonal neighbours hold `v`.
    return num_eq(x[adj4(p)], v)

def n_adj8(x, p, v):
    # How many of the (at most) 8 surrounding cells hold `v`.
    return num_eq(x[adj8(p)], v)

def n_diag4(x, p, v):
    return num_eq(x[diag4(p)], v)

def n_around(x, p, v):
    # The cell itself plus its 4 orthogonal neighbours.
    return num_eq(x[cell_of(p) and adj4(p)], v)


# -- local shape constraints --------------------------------------------------

def no2x2(x, v):
    # Forbid any 2x2 block whose four cells all hold `v`.
    for w in slide(2, 2):
        num_eq(x[w], v) < 4

def no_run(x, v, n):
    # Forbid n consecutive cells holding `v`, horizontally and vertically.
    for w in slide(n, 1):
        num_eq(x[w], v) < n
    for w in slide(1, n):
        num_eq(x[w], v) < n

def no_adjacent(x, v):
    # Cells holding `v` are never orthogonally adjacent.
    for p in cells():
        eq(x, p, v) => n_adj4(x, p, v) == 0

def no_diag_adjacent(x, v):
    for p in cells():
        eq(x, p, v) => n_diag4(x, p, v) == 0


# -- connectivity -------------------------------------------------------------

def connected(x, v):
    # All cells holding `v` form (at most) one orthogonally connected group.
    return cc_count(x, v) <= 1

def connected8(x, v):
    # ... one diagonally connected group.
    return cc8_count(x, v) <= 1

def group_count(x, v, n):
    return cc_count(x, v) == n


# -- rectangles ---------------------------------------------------------------

def is_rect_group(x, v):
    # Every connected group of `v` cells is a rectangle: equivalently no group
    # contains an L-shaped corner, i.e. in each 2x2 window the count of `v`
    # cells is never exactly 3.
    for w in slide(2, 2):
        num_eq(x[w], v) != 3


# -- generic clue plumbing ----------------------------------------------------

def clue_cells(c):
    # The cells that actually carry a clue value.
    return defined(c)

def before(p, q):
    # Compile-time reading order comparison, for "each unordered pair once".
    if row_of(p) < row_of(q):
        return true
    if row_of(p) > row_of(q):
        return false
    return col_of(p) < col_of(q)

def step(p, d):
    # The neighbour of `p` in direction d (UP/DOWN/LEFT/RIGHT); empty at the
    # board edge, so guard with `.size == 0`.
    if d == UP:
        return shift(p, -1, 0)
    if d == DOWN:
        return shift(p, 1, 0)
    if d == LEFT:
        return shift(p, 0, -1)
    return shift(p, 0, 1)
