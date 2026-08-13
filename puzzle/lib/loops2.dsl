# ============================================================================
# loops2.dsl — extra loop helpers (self-cross, rectangles, slither segments,
# terrain flags).  Does not modify loops.dsl.
#
#   import "loops2"
# ============================================================================

import "loops"


def marked(c, p):
    if has_value(c, p):
        return at(c, p) != 0
    return false

def no_outer_links(e):
    for p in cells():
        let up = shift(p, -1, 0)
        let down = shift(p, 1, 0)
        let left = shift(p, 0, -1)
        let right = shift(p, 0, 1)
        if up.size == 0:
            link_up(e, p) == 0
        if down.size == 0:
            link_down(e, p) == 0
        if left.size == 0:
            link_left(e, p) == 0
        if right.size == 0:
            link_right(e, p) == 0

def on_track(e, p):
    return cdeg(e, p) == 2 or cdeg(e, p) == 4

def is_cross(e, p):
    return cdeg(e, p) == 4

def deg024(e):
    no_outer_links(e)
    for p in cells():
        let d = cdeg(e, p)
        d == 0 or d == 2 or d == 4

def cross_loop(e):
    # One connected loop; cells may be unused, a bend/straight, or a crossing.
    connect_links(e)
    for p in cells():
        let d = cdeg(e, p)
        d == 0 or d == 2 or d == 4

def full_cross_loop(e):
    connect_links(e)
    for p in cells():
        let d = cdeg(e, p)
        d == 2 or d == 4


# -- slitherlink segment length (Line of Sight) -------------------------------

def h_seg_len(e, er, ec):
    let left = 0
    let alive = true
    for p in dir(cell(0, ec), LEFT):
        let alive = alive and (at(e, edge("H", er, col_of(p))) == 1)
        let left = left + b2i(alive)
    let right = 0
    let alive2 = true
    for p in dir(cell(0, ec), RIGHT):
        let alive2 = alive2 and (at(e, edge("H", er, col_of(p))) == 1)
        let right = right + b2i(alive2)
    return 1 + left + right

def v_seg_len(e, er, ec):
    let up = 0
    let alive = true
    for p in dir(cell(er, 0), UP):
        let alive = alive and (at(e, edge("V", row_of(p), ec)) == 1)
        let up = up + b2i(alive)
    let down = 0
    let alive2 = true
    for p in dir(cell(er, 0), DOWN):
        let alive2 = alive2 and (at(e, edge("V", row_of(p), ec)) == 1)
        let down = down + b2i(alive2)
    return 1 + up + down

def edge_seg_len(e, p, d):
    if d == UP:
        return h_seg_len(e, row_of(p), col_of(p))
    if d == DOWN:
        return h_seg_len(e, row_of(p) + 1, col_of(p))
    if d == LEFT:
        return v_seg_len(e, row_of(p), col_of(p))
    return v_seg_len(e, row_of(p), col_of(p) + 1)

def nearest_seg_len(e, p, d):
    let found = false
    let length = 0
    let hit0 = link_dir(e, p, d) == 1
    let length = ite(hit0, edge_seg_len(e, p, d), 0)
    let found = hit0
    for q in dir(p, d):
        let hit = link_dir(e, q, d) == 1
        let length = ite(found, length, ite(hit, edge_seg_len(e, q, d), 0))
        let found = found or hit
    return ite(found, length, 0)


# -- rectangular cell-center loops -------------------------------------------

def rect_perimeter_ok(e, r1, c1, r2, c2):
    let ok = true
    let tl = cell(r1, c1)
    for q in dir(tl, RIGHT):
        if col_of(q) <= c2:
            let ok = ok and (link_left(e, q) == 1)
    for q in dir(tl, DOWN):
        if row_of(q) <= r2:
            let ok = ok and (link_up(e, q) == 1)
    let tr = cell(r1, c2)
    for q in dir(tr, DOWN):
        if row_of(q) <= r2:
            let ok = ok and (link_up(e, q) == 1)
    let bl = cell(r2, c1)
    for q in dir(bl, RIGHT):
        if col_of(q) <= c2:
            let ok = ok and (link_left(e, q) == 1)
    return ok

def on_rect_perim(r1, c1, r2, c2, p):
    let r = row_of(p)
    let c = col_of(p)
    let on_h = (r == r1 or r == r2) and c >= c1 and c <= c2
    let on_v = (c == c1 or c == c2) and r >= r1 and r <= r2
    return on_h or on_v

def in_rect_strict(r1, c1, r2, c2, p):
    let r = row_of(p)
    let c = col_of(p)
    return r > r1 and r < r2 and c > c1 and c < c2

def hlink_rect_count(e, p):
    let r = row_of(p)
    let c = col_of(p)
    let n = 0
    for a in cells():
        for b in cells():
            if row_of(a) < row_of(b):
                if col_of(a) < col_of(b):
                    let r1 = row_of(a)
                    let c1 = col_of(a)
                    let r2 = row_of(b)
                    let c2 = col_of(b)
                    if (r == r1 or r == r2) and c >= c1 and c < c2:
                        let n = n + b2i(rect_perimeter_ok(e, r1, c1, r2, c2))
    return n

def vlink_rect_count(e, p):
    let r = row_of(p)
    let c = col_of(p)
    let n = 0
    for a in cells():
        for b in cells():
            if row_of(a) < row_of(b):
                if col_of(a) < col_of(b):
                    let r1 = row_of(a)
                    let c1 = col_of(a)
                    let r2 = row_of(b)
                    let c2 = col_of(b)
                    if (c == c1 or c == c2) and r >= r1 and r < r2:
                        let n = n + b2i(rect_perimeter_ok(e, r1, c1, r2, c2))
    return n

def corner_rect_count(e, p):
    let r = row_of(p)
    let c = col_of(p)
    let n = 0
    for a in cells():
        for b in cells():
            if row_of(a) < row_of(b):
                if col_of(a) < col_of(b):
                    let r1 = row_of(a)
                    let c1 = col_of(a)
                    let r2 = row_of(b)
                    let c2 = col_of(b)
                    if (r == r1 or r == r2) and (c == c1 or c == c2):
                        let n = n + b2i(rect_perimeter_ok(e, r1, c1, r2, c2))
    return n

def on_drawn_rect(e, p):
    let hit = false
    for a in cells():
        for b in cells():
            if row_of(a) < row_of(b):
                if col_of(a) < col_of(b):
                    if on_rect_perim(row_of(a), col_of(a), row_of(b), col_of(b), p):
                        let hit = hit or rect_perimeter_ok(e, row_of(a), col_of(a), row_of(b), col_of(b))
    return hit

def inside_drawn_count(e, p):
    let n = 0
    for a in cells():
        for b in cells():
            if row_of(a) < row_of(b):
                if col_of(a) < col_of(b):
                    if in_rect_strict(row_of(a), col_of(a), row_of(b), col_of(b), p):
                        let n = n + b2i(rect_perimeter_ok(e, row_of(a), col_of(a), row_of(b), col_of(b)))
    return n

def rectangular_loops(e):
    # Selected cell-center links are a disjoint-edge union of rectangle
    # perimeters.  Degree-4 cells are crossings; rectangle corners are unique.
    no_outer_links(e)
    for p in cells():
        let q = shift(p, 0, 1)
        if q.size != 0:
            hlink_rect_count(e, p) == link_right(e, p)
        let q2 = shift(p, 1, 0)
        if q2.size != 0:
            vlink_rect_count(e, p) == link_down(e, p)
        corner_rect_count(e, p) <= 1


# -- 8-neighbour on-loop occupancy (Tapa-like Loop) --------------------------

def nb_on(e, p, dr, dc):
    let q = shift(p, dr, dc)
    if q.size == 0:
        return 0
    return b2i(on_loop(e, q))

def around8_sum(e, p):
    let s = nb_on(e, p, -1, 0) + nb_on(e, p, -1, 1) + nb_on(e, p, 0, 1) + nb_on(e, p, 1, 1)
    let s = s + nb_on(e, p, 1, 0) + nb_on(e, p, 1, -1) + nb_on(e, p, 0, -1) + nb_on(e, p, -1, -1)
    return s

def around8_trans(e, p):
    let b0 = nb_on(e, p, -1, 0)
    let b1 = nb_on(e, p, -1, 1)
    let b2 = nb_on(e, p, 0, 1)
    let b3 = nb_on(e, p, 1, 1)
    let b4 = nb_on(e, p, 1, 0)
    let b5 = nb_on(e, p, 1, -1)
    let b6 = nb_on(e, p, 0, -1)
    let b7 = nb_on(e, p, -1, -1)
    let t = b2i(b0 != b1) + b2i(b1 != b2) + b2i(b2 != b3) + b2i(b3 != b4)
    let t = t + b2i(b4 != b5) + b2i(b5 != b6) + b2i(b6 != b7) + b2i(b7 != b0)
    return t

def around8_single(e, p, n):
    around8_sum(e, p) == n
    if n == 0:
        around8_trans(e, p) == 0
    else:
        if n == 8:
            around8_trans(e, p) == 0
        else:
            around8_trans(e, p) == 2

def around8_bits(e, p):
    return [nb_on(e, p, -1, 0), nb_on(e, p, -1, 1), nb_on(e, p, 0, 1), nb_on(e, p, 1, 1), nb_on(e, p, 1, 0), nb_on(e, p, 1, -1), nb_on(e, p, 0, -1), nb_on(e, p, -1, -1)]

def tapaloop_clue(e, n, n2, n3, n4, p):
    let bits = around8_bits(e, p)
    if not has_value(n2, p) and at(n, p) < 0:
        runs_cycle(bits, 0) or runs_cycle(bits, 0 - 1)
    else:
        let lens = [at(n, p)]
        if has_value(n2, p):
            let lens = lens and [at(n2, p)]
        if has_value(n3, p):
            let lens = lens and [at(n3, p)]
        if has_value(n4, p):
            let lens = lens and [at(n4, p)]
        runs_cycle(bits, lens)


# -- water / ice along-loop local --------------------------------------------

def loop_water_neighbours(e, w, p):
    let nb = 0
    for q in adj4(p):
        if marked(w, q):
            let nb = nb + link_between(e, p, q)
    return nb
