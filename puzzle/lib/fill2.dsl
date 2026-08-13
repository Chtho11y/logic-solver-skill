# ============================================================================
# fill2.dsl — extra helpers for the remaining 填写 family.
#
#   import "fill2"
# ============================================================================

import "fill"
import "outside"


def values_param(fallback):
    if has_param("values"):
        return param("values")
    return fallback


def board_n():
    return rows.size


def allowed_or_empty(x, p, vals):
    let ok = b2i(at(x, p) == 0)
    for v in vals:
        let ok = ok + b2i(at(x, p) == v)
    ok == 1


def each_once(x, vals):
    for r in rows:
        for v in vals:
            num_eq(x[r], v) == 1
    for c in cols:
        for v in vals:
            num_eq(x[c], v) == 1


def each_at_most_once(x, vals):
    for r in rows:
        for v in vals:
            num_eq(x[r], v) <= 1
    for c in cols:
        for v in vals:
            num_eq(x[c], v) <= 1


def latin_n(x, n):
    for r in rows:
        distinct(x[r])
        for p in r:
            at(x, p) >= 1
            at(x, p) <= n
    for c in cols:
        distinct(x[c])


def nonzero_unique(x):
    for r in rows:
        for p in r:
            for q in r:
                if before(p, q):
                    not (at(x, p) > 0 and at(x, p) == at(x, q))
    for c in cols:
        for p in c:
            for q in c:
                if before(p, q):
                    not (at(x, p) > 0 and at(x, p) == at(x, q))


def kropki_consec(a, b):
    return abs(a - b) == 1


def kropki_double(a, b):
    return (a * 2 == b) or (b * 2 == a)


def first_nonzero(x, line):
    let seen = 0
    let first = 0
    for p in line:
        let first = ite(seen == 0, ite(at(x, p) != 0, at(x, p), 0), first)
        let seen = ite(at(x, p) != 0, 1, seen)
    return first


def vis_count(x, line):
    let vis = 0
    let mx = 0
    for p in line:
        let vis = vis + b2i(at(x, p) > mx)
        let mx = ite(at(x, p) > mx, at(x, p), mx)
    return vis


def reverse_row_cell(p):
    return cell(row_of(p), count(row(row_of(p))) - 1 - col_of(p))


def reverse_col_cell(p):
    return cell(count(col(col_of(p))) - 1 - row_of(p), col_of(p))


def vis_count_row_rev(x, line):
    let vis = 0
    let mx = 0
    for p in line:
        let q = reverse_row_cell(p)
        let vis = vis + b2i(at(x, q) > mx)
        let mx = ite(at(x, q) > mx, at(x, q), mx)
    return vis


def vis_count_col_rev(x, line):
    let vis = 0
    let mx = 0
    for p in line:
        let q = reverse_col_cell(p)
        let vis = vis + b2i(at(x, q) > mx)
        let mx = ite(at(x, q) > mx, at(x, q), mx)
    return vis


def first_nonzero_row_rev(x, line):
    let seen = 0
    let first = 0
    for p in line:
        let q = reverse_row_cell(p)
        let first = ite(seen == 0, ite(at(x, q) != 0, at(x, q), 0), first)
        let seen = ite(at(x, q) != 0, 1, seen)
    return first


def first_nonzero_col_rev(x, line):
    let seen = 0
    let first = 0
    for p in line:
        let q = reverse_col_cell(p)
        let first = ite(seen == 0, ite(at(x, q) != 0, at(x, q), 0), first)
        let seen = ite(at(x, q) != 0, 1, seen)
    return first


def magic_line_value(x, line):
    let total = 0
    let acc = 0
    for p in line:
        let d = at(x, p)
        let total = ite(d == 0, total + acc, total)
        let acc = ite(d == 0, 0, acc * 10 + d)
    return total + acc


def apply_run_sums(x, line, k):
    if no_clue(k):
        true
    else:
        let clues = k
        if not is_list(k):
            let clues = [k]
        let rid = 0
        let prev = 0
        for p in line:
            let f = b2i(at(x, p) != 0)
            let rid = rid + ite(f == 1 and prev == 0, 1, 0)
            let prev = f
        rid == clues.size
        let j = 0
        for clue in clues:
            let j = j + 1
            if clue != "?":
                let s = 0
                let rid2 = 0
                let prev2 = 0
                for p in line:
                    let f = b2i(at(x, p) != 0)
                    let rid2 = rid2 + ite(f == 1 and prev2 == 0, 1, 0)
                    let prev2 = f
                    let s = s + ite(rid2 == j, at(x, p), 0)
                s == clue


def between_v_edge(p, q):
    # Vertical lattice edge between two same-row neighbours (p left of q).
    return edge("V", row_of(p), col_of(q))


def between_h_edge(p, q):
    # Horizontal lattice edge between two same-col neighbours (p above q).
    return edge("H", row_of(q), col_of(p))


def region_border_len(id1, id2):
    let n = 0
    for p in cells():
        for q in adj4(p):
            if before(p, q):
                if region_id(p) == id1 and region_id(q) == id2:
                    let n = n + 1
                if region_id(p) == id2 and region_id(q) == id1:
                    let n = n + 1
    return n


def regions_share_border(id1, id2):
    return region_border_len(id1, id2) > 0


def one_per_region(x):
    for reg in regions:
        num_eq(x[reg], 0) == reg.size - 1


def slash_degree(g, v):
    # How many cell-diagonals touch corner `v`. g: 1=╲ 2=╱
    let d = 0
    let r = row_of(v)
    let c = col_of(v)
    if r < rows.size and c < cols.size:
        let d = d + b2i(at(g, cell(r, c)) == 1)
    if r < rows.size and c > 0:
        let d = d + b2i(at(g, cell(r, c - 1)) == 2)
    if r > 0 and c < cols.size:
        let d = d + b2i(at(g, cell(r - 1, c)) == 2)
    if r > 0 and c > 0:
        let d = d + b2i(at(g, cell(r - 1, c - 1)) == 1)
    return d
