# ============================================================================
# place2.dsl — helpers for remaining 放置 / 分区 rules (shape fingerprints,
# 180° symmetry, translation matching). Does not modify regions.dsl.
#
#   import "place2"
#
# Pentomino letters (free, rotations/flips identified):
#   F=1 I=2 L=3 N=4 P=5 T=6 U=7 V=8 W=9 X=10 Y=11 Z=12
# Tetromino letters: I=1 O=2 T=3 L=4 S=5
# ============================================================================

import "regions"


def is_root(c, p):
    return at(c, p) == row_of(p) * cols.size + col_of(p)

def region_full2x2(c, p):
    return cc_full2x2(c, p)

def region_deg_count(c, p, d):
    return cc_deg_count(c, p, d)

def region_bbox_h(c, p):
    return at(c.bbox_h, p)

def region_bbox_w(c, p):
    return at(c.bbox_w, p)

def region_bbox_corners(c, p):
    return cc_corner_count(c, p)

def ba5(c, p):
    let h = region_bbox_h(c, p)
    let w = region_bbox_w(c, p)
    return (h == 1 and w == 5) or (h == 5 and w == 1)

def ba6(c, p):
    let h = region_bbox_h(c, p)
    let w = region_bbox_w(c, p)
    return (h == 2 and w == 3) or (h == 3 and w == 2)

def ba8(c, p):
    let h = region_bbox_h(c, p)
    let w = region_bbox_w(c, p)
    return (h == 2 and w == 4) or (h == 4 and w == 2)

def ba9(c, p):
    return region_bbox_h(c, p) == 3 and region_bbox_w(c, p) == 3

def pent_type(c, p):
    # Unique fingerprints of the 12 free pentominoes (size-5 CC region).
    let n3 = region_notch_count(c, p)
    let f4 = region_full2x2(c, p)
    let d1 = region_deg_count(c, p, 1)
    let d3 = region_deg_count(c, p, 3)
    let d4 = region_deg_count(c, p, 4)
    let cn = region_bbox_corners(c, p)
    let t = 0
    let t = t + 1 * b2i(n3 == 2 and d1 == 3 and d3 == 1 and ba9(c, p) and cn == 1)
    let t = t + 2 * b2i(ba5(c, p))
    let t = t + 3 * b2i(n3 == 1 and d1 == 2 and ba8(c, p) and cn == 3)
    let t = t + 4 * b2i(n3 == 2 and d1 == 2 and ba8(c, p))
    let t = t + 5 * b2i(f4 >= 1)
    let t = t + 6 * b2i(n3 == 2 and d1 == 3 and d3 == 1 and ba9(c, p) and cn == 2)
    let t = t + 7 * b2i(n3 == 2 and ba6(c, p) and f4 == 0)
    let t = t + 8 * b2i(n3 == 1 and ba9(c, p))
    let t = t + 9 * b2i(n3 == 3)
    let t = t + 10 * b2i(d4 >= 1)
    let t = t + 11 * b2i(n3 == 1 and d1 == 3 and ba8(c, p))
    let t = t + 12 * b2i(n3 == 2 and d1 == 2 and ba9(c, p))
    return t

def tet_type(c, p):
    let n3 = region_notch_count(c, p)
    let f4 = region_full2x2(c, p)
    let d3 = region_deg_count(c, p, 3)
    let h = region_bbox_h(c, p)
    let w = region_bbox_w(c, p)
    let t = 0
    let t = t + 1 * b2i((h == 1 and w == 4) or (h == 4 and w == 1))
    let t = t + 2 * b2i(f4 >= 1)
    let t = t + 3 * b2i(d3 >= 1)
    let t = t + 4 * b2i(n3 == 1 and d3 == 0)
    let t = t + 5 * b2i(n3 == 2 and d3 == 0)
    return t

def tromino_type(c, p):
    # Translation classes of the trominoes (I two ways, L four missing-corner ids).
    let h = region_bbox_h(c, p)
    let w = region_bbox_w(c, p)
    let minr = row_of(p)
    let maxr = row_of(p)
    let minc = col_of(p)
    let maxc = col_of(p)
    for q in cells():
        let minr = ite(at(c, q) == at(c, p) and row_of(q) < minr, row_of(q), minr)
        let maxr = ite(at(c, q) == at(c, p) and row_of(q) > maxr, row_of(q), maxr)
        let minc = ite(at(c, q) == at(c, p) and col_of(q) < minc, col_of(q), minc)
        let maxc = ite(at(c, q) == at(c, p) and col_of(q) > maxc, col_of(q), maxc)
    let c00 = 0
    let c01 = 0
    let c10 = 0
    let c11 = 0
    for q in cells():
        let here = at(c, q) == at(c, p)
        let c00 = c00 + b2i(here and row_of(q) == minr and col_of(q) == minc)
        let c01 = c01 + b2i(here and row_of(q) == minr and col_of(q) == maxc)
        let c10 = c10 + b2i(here and row_of(q) == maxr and col_of(q) == minc)
        let c11 = c11 + b2i(here and row_of(q) == maxr and col_of(q) == maxc)
    let t = 2 * b2i(h == 2 and w == 2 and c00 == 0)
    let t = t + 3 * b2i(h == 2 and w == 2 and c01 == 0)
    let t = t + 4 * b2i(h == 2 and w == 2 and c10 == 0)
    let t = t + 5 * b2i(h == 2 and w == 2 and c11 == 0)
    let t = ite(h == 1 and w == 3, 0, t)
    let t = ite(h == 3 and w == 1, 1, t)
    return t


# -- 8-element dihedral transforms of (dr, dc) relative to an origin ---------

def tr_r(dr, dc, t):
    return tr(dr, dc, t)[0]

def tr_c(dr, dc, t):
    return tr(dr, dc, t)[1]

def region_match_tr(c, a, b, t):
    # Region of `a`, rotated/flipped by t about `a`, equals region of `b` about `b`.
    let ok = true
    for s in cells():
        let s2 = shift(b, tr_r(row_of(s) - row_of(a), col_of(s) - col_of(a), t), tr_c(row_of(s) - row_of(a), col_of(s) - col_of(a), t))
        if s2.size == 0:
            let ok = ok and (at(c, s) != at(c, a))
        if s2.size == 1:
            let ok = ok and ((at(c, s) == at(c, a)) == (at(c, s2) == at(c, b)))
    return ok

def freely_congruent(c, p, q):
    let hit = false
    for t in [0, 1, 2, 3, 4, 5, 6, 7]:
        for b in cells():
            let hit = hit or (at(c, b) == at(c, q) and region_match_tr(c, p, b, t))
    return hit

def translation_congruent(c, p, q):
    return region_match_tr(c, p, q, 0)

def fits_in_at(c, a, b):
    # Translate region of `a` so `a` maps to `b`; is it a subset of region of `b`?
    let ok = true
    for s in cells():
        let s2 = shift(s, row_of(b) - row_of(a), col_of(b) - col_of(a))
        if s2.size == 0:
            let ok = ok and (at(c, s) != at(c, a))
        if s2.size == 1:
            let ok = ok and (at(c, s) != at(c, a) or at(c, s2) == at(c, b))
    return ok

def can_fit_in(c, p, q):
    let hit = false
    for b in cells():
        let hit = hit or (at(c, b) == at(c, q) and fits_in_at(c, p, b))
    return hit

def subset_match_tr(c, g, a, b, t, va, vb):
    # Cells of region a with g==va, transformed about a, equal cells of region b with g==vb.
    let ok = true
    for s in cells():
        let in_a = at(c, s) == at(c, a) and at(g, s) == va
        let s2 = shift(b, tr_r(row_of(s) - row_of(a), col_of(s) - col_of(a), t), tr_c(row_of(s) - row_of(a), col_of(s) - col_of(a), t))
        if s2.size == 0:
            let ok = ok and not in_a
        if s2.size == 1:
            let in_b = at(c, s2) == at(c, b) and at(g, s2) == vb
            let ok = ok and (in_a == in_b)
    return ok

def parts_congruent(c, g, p):
    let hit = false
    for a in cells():
        for b in cells():
            for t in [0, 1, 2, 3, 4, 5, 6, 7]:
                let hit = hit or (at(c, a) == at(c, p) and at(g, a) == 1 and at(c, b) == at(c, p) and at(g, b) == 0 and subset_match_tr(c, g, a, b, t, 1, 0))
    return hit

def regions_touch(c, p, q):
    let hit = false
    for u in cells():
        for v in adj4(u):
            let hit = hit or (at(c, u) == at(c, p) and at(c, v) == at(c, q))
    return hit

def color_count_in(c, g, p, v):
    let total = 0
    for q in cells():
        let total = total + b2i(at(c, q) == at(c, p) and at(g, q) == v)
    return total

def color_pairs_in(c, g, p, v):
    let total = 0
    for q in cells():
        for r in adj4(q):
            if before(q, r):
                let total = total + b2i(at(c, q) == at(c, p) and at(c, r) == at(c, p) and at(g, q) == v and at(g, r) == v)
    return total


# -- 180° rotational symmetry of a solved region (unknown centre) ------------

def region_sym_shift(c, p, q, dr, dc):
    if not in_grid(q, dr, dc):
        return at(c, q) != at(c, p)
    return (at(c, q) == at(c, p)) == (at(c, shift(q, dr, dc)) == at(c, p))

def region_sym_cell(c, p, t):
    return all_where(cells(), fn (q) -> region_sym_shift(c, p, q, 2 * row_of(t) - 2 * row_of(q), 2 * col_of(t) - 2 * col_of(q)))

def region_sym_vertex(c, p, v):
    return all_where(cells(), fn (q) -> region_sym_shift(c, p, q, 2 * row_of(v) - 1 - 2 * row_of(q), 2 * col_of(v) - 1 - 2 * col_of(q)))

def region_sym_pair(c, p, a, b):
    # 180° about the midpoint of adjacent cells a, b.
    return all_where(cells(), fn (q) -> region_sym_shift(c, p, q, row_of(a) + row_of(b) - 2 * row_of(q), col_of(a) + col_of(b) - 2 * col_of(q)))

def has_180_sym(c, p):
    let ok = false
    for t in cells():
        let ok = ok or region_sym_cell(c, p, t)
    for v in corners():
        let ok = ok or region_sym_vertex(c, p, v)
    for e in edges():
        let sides = cell_of(e)
        if sides.size == 2:
            for a in sides:
                for b in sides:
                    if before(a, b):
                        let ok = ok or region_sym_pair(c, p, a, b)
    return ok


# -- mirrors (axis = the line of an edge between cells a and b) --------------

def mirror_image(c, a, b, p, q):
    # Reflecting region of p across the axis of edge a|b yields region of q.
    let ok = true
    if row_of(a) == row_of(b):
        for s in cells():
            let s2 = shift(s, 0, col_of(a) + col_of(b) - 2 * col_of(s))
            if s2.size == 0:
                let ok = ok and (at(c, s) != at(c, p))
            if s2.size == 1:
                let ok = ok and ((at(c, s) == at(c, p)) == (at(c, s2) == at(c, q)))
    else:
        for s in cells():
            let s2 = shift(s, row_of(a) + row_of(b) - 2 * row_of(s), 0)
            if s2.size == 0:
                let ok = ok and (at(c, s) != at(c, p))
            if s2.size == 1:
                let ok = ok and ((at(c, s) == at(c, p)) == (at(c, s2) == at(c, q)))
    return ok


# -- shade / partition coupling ----------------------------------------------

def shade_matches_cc(x, c):
    for p in cells():
        for q in adj4(p):
            if before(p, q):
                (at(x, p) == at(x, q)) == (at(c, p) == at(c, q))

def nearest_eq_dist(x, p, d, v):
    let dist = 0
    let seen = false
    let k = 0
    for q in dir(p, d):
        let k = k + 1
        let hit = at(x, q) == v
        let dist = ite(seen, dist, ite(hit, k, dist))
        let seen = seen or hit
    return dist

def nearest_nonzero_dist(x, p, d):
    let dist = 0
    let seen = false
    let k = 0
    for q in dir(p, d):
        let k = k + 1
        let hit = at(x, q) != 0
        let dist = ite(seen, dist, ite(hit, k, dist))
        let seen = seen or hit
    return dist

def nearest_nonzero_val(x, p, d):
    let val = 0
    let seen = false
    for q in dir(p, d):
        let hit = at(x, q) != 0
        let val = ite(seen, val, ite(hit, at(x, q), val))
        let seen = seen or hit
    return val

def myopia_bits(x, p, bits, v):
    let du = nearest_eq_dist(x, p, UP, v)
    let dd = nearest_eq_dist(x, p, DOWN, v)
    let dl = nearest_eq_dist(x, p, LEFT, v)
    let dr = nearest_eq_dist(x, p, RIGHT, v)
    let inf = rows.size + cols.size + 1
    let m = inf
    let m = ite(du > 0 and du < m, du, m)
    let m = ite(dd > 0 and dd < m, dd, m)
    let m = ite(dl > 0 and dl < m, dl, m)
    let m = ite(dr > 0 and dr < m, dr, m)
    let has_u = bits % 2 == 1
    let has_d = (bits / 2) % 2 == 1
    let has_l = (bits / 4) % 2 == 1
    let has_r = (bits / 8) % 2 == 1
    if has_u:
        du > 0 and du == m
    if not has_u:
        du == 0 or du > m
    if has_d:
        dd > 0 and dd == m
    if not has_d:
        dd == 0 or dd > m
    if has_l:
        dl > 0 and dl == m
    if not has_l:
        dl == 0 or dl > m
    if has_r:
        dr > 0 and dr == m
    if not has_r:
        dr == 0 or dr > m

def vertex_diag_kiss(x, ids, v):
    # Two covered cells of different 4-components meet diagonally at corner v.
    let kiss = false
    for p in cell_of(v):
        for q in cell_of(v):
            if row_of(p) != row_of(q) and col_of(p) != col_of(q):
                let kiss = kiss or (at(x, p) == 1 and at(x, q) == 1 and at(ids, p) != at(ids, q))
    return kiss

def h_run_len(c, p):
    # Maximal horizontal run through p inside p's region.
    let n = 1
    let stop = false
    for q in dir(p, LEFT):
        let stop = stop or (at(c, q) != at(c, p))
        let n = n + b2i(not stop)
    let stop2 = false
    for q in dir(p, RIGHT):
        let stop2 = stop2 or (at(c, q) != at(c, p))
        let n = n + b2i(not stop2)
    return n

def v_run_len(c, p):
    let n = 1
    let stop = false
    for q in dir(p, UP):
        let stop = stop or (at(c, q) != at(c, p))
        let n = n + b2i(not stop)
    let stop2 = false
    for q in dir(p, DOWN):
        let stop2 = stop2 or (at(c, q) != at(c, p))
        let n = n + b2i(not stop2)
    return n

def is_h_run_start(c, p):
    let q = shift(p, 0, -1)
    if q.size == 0:
        return true
    return at(c, q) != at(c, p)

def is_v_run_start(c, p):
    let q = shift(p, -1, 0)
    if q.size == 0:
        return true
    return at(c, q) != at(c, p)

def region_has_run(c, p, k):
    let hit = false
    for q in cells():
        let hit = hit or (is_h_run_start(c, q) and at(c, q) == at(c, p) and h_run_len(c, q) == k)
        let hit = hit or (is_v_run_start(c, q) and at(c, q) == at(c, p) and v_run_len(c, q) == k)
    return hit

def run_matches_clues(c, p, L, n1, n2, n3):
    let match = false
    if has_value(n1, p):
        let match = match or (L == at(n1, p))
    if has_value(n2, p):
        let match = match or (L == at(n2, p))
    if has_value(n3, p):
        let match = match or (L == at(n3, p))
    return match

def every_run_in_clues(c, p, n1, n2, n3):
    let ok = true
    for q in cells():
        let hit_h = is_h_run_start(c, q) and at(c, q) == at(c, p)
        let hit_v = is_v_run_start(c, q) and at(c, q) == at(c, p)
        let ok = ok and (not hit_h or run_matches_clues(c, p, h_run_len(c, q), n1, n2, n3))
        let ok = ok and (not hit_v or run_matches_clues(c, p, v_run_len(c, q), n1, n2, n3))
    return ok
