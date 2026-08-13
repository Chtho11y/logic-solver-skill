# scrabble — 拼词
# 字母格连通。每个长度≥2 的横/纵段都是词表中的单词，且每个单词恰好一次。

import "fill2"

for p in cells():
    (at(f, p) == 1) == (at(x, p) > 0)

connected(f, 1)

def row_run(r, c0, c1):
    let filled = 1
    for c in cols:
        let cc = col_of(c[0])
        if c0 <= cc and cc <= c1:
            let filled = filled * b2i(at(x, cell(r, cc)) > 0)
        if cc == c0 - 1:
            let filled = filled * b2i(at(x, cell(r, cc)) == 0)
        if cc == c1 + 1:
            let filled = filled * b2i(at(x, cell(r, cc)) == 0)
    return filled

def col_run(c, r0, r1):
    let filled = 1
    for rr in rows:
        let r = row_of(rr[0])
        if r0 <= r and r <= r1:
            let filled = filled * b2i(at(x, cell(r, c)) > 0)
        if r == r0 - 1:
            let filled = filled * b2i(at(x, cell(r, c)) == 0)
        if r == r1 + 1:
            let filled = filled * b2i(at(x, cell(r, c)) == 0)
    return filled

def matches_row(r, c0, word):
    let ok = 1
    let i = 0
    for ch in word:
        let ok = ok * b2i(at(x, cell(r, c0 + i)) == ch)
        let i = i + 1
    return ok

def matches_col(c, r0, word):
    let ok = 1
    let i = 0
    for ch in word:
        let ok = ok * b2i(at(x, cell(r0 + i, c)) == ch)
        let i = i + 1
    return ok

if has_param("words"):
    let words = param("words")
    for w in words:
        if w.size >= 2:
            let cnt = 0
            for r in rows:
                let rr = row_of(r[0])
                for c in cols:
                    let c0 = col_of(c[0])
                    let c1 = c0 + w.size - 1
                    if c1 < cols.size:
                        let cnt = cnt + row_run(rr, c0, c1) * matches_row(rr, c0, w)
            for c in cols:
                let cc = col_of(c[0])
                for r in rows:
                    let r0 = row_of(r[0])
                    let r1 = r0 + w.size - 1
                    if r1 < rows.size:
                        let cnt = cnt + col_run(cc, r0, r1) * matches_col(cc, r0, w)
            cnt == 1
    for r in rows:
        let rr = row_of(r[0])
        for c in cols:
            let c0 = col_of(c[0])
            for c2 in cols:
                let c1 = col_of(c2[0])
                if c1 >= c0 + 1:
                    let isrun = row_run(rr, c0, c1)
                    let hit = 0
                    for w in words:
                        if w.size == c1 - c0 + 1:
                            let hit = hit + matches_row(rr, c0, w)
                    isrun == 1 => hit >= 1
    for c in cols:
        let cc = col_of(c[0])
        for r in rows:
            let r0 = row_of(r[0])
            for r2 in rows:
                let r1 = row_of(r2[0])
                if r1 >= r0 + 1:
                    let isrun = col_run(cc, r0, r1)
                    let hit = 0
                    for w in words:
                        if w.size == r1 - r0 + 1:
                            let hit = hit + matches_col(cc, r0, w)
                    isrun == 1 => hit >= 1
