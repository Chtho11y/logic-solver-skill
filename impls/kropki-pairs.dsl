# 拉丁方 1..N。只对给出的黑白点施加差 1 / 比 1:2；未给出的邻格不限制。
import "fill"

def kropki_pairs(x, d):
    latin_1_to_n(x)

    for e in clue_cells(d):
        let cs = cell_of(e)
        if cs.size == 2:
            let a = x[cs[0]]
            let b = x[cs[1]]
            if d[e] == 1:
                kropki_white(a, b)
            else:
                kropki_black(a, b)
        else:
            false

kropki_pairs(x, d)
