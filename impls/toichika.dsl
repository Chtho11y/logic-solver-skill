# toichika — 山盟海誓
# 每区一个箭头。箭头两两对射、中间无其他箭头；配对两区无公共边界。

import "fill2"

for p in cells():
    at(a, p) == 8 or at(a, p) <= 3

for reg in regions:
    num_eq(a[reg], 8) == reg.size - 1

for p in cells():
    let partners = 0
    for q in cells():
        if row_of(p) == row_of(q) and col_of(p) < col_of(q):
            let mid = 0
            for s in row(row_of(p)):
                if col_of(p) < col_of(s) and col_of(s) < col_of(q):
                    let mid = mid + b2i(at(a, s) != 8)
            let ispair = b2i(at(a, p) == RIGHT and at(a, q) == LEFT and mid == 0)
            if regions_share_border(region_id(p), region_id(q)):
                ispair == 0
            let partners = partners + ispair
        if row_of(p) == row_of(q) and col_of(q) < col_of(p):
            let mid = 0
            for s in row(row_of(p)):
                if col_of(q) < col_of(s) and col_of(s) < col_of(p):
                    let mid = mid + b2i(at(a, s) != 8)
            let ispair = b2i(at(a, q) == RIGHT and at(a, p) == LEFT and mid == 0)
            if regions_share_border(region_id(p), region_id(q)):
                ispair == 0
            let partners = partners + ispair
        if col_of(p) == col_of(q) and row_of(p) < row_of(q):
            let mid = 0
            for s in col(col_of(p)):
                if row_of(p) < row_of(s) and row_of(s) < row_of(q):
                    let mid = mid + b2i(at(a, s) != 8)
            let ispair = b2i(at(a, p) == DOWN and at(a, q) == UP and mid == 0)
            if regions_share_border(region_id(p), region_id(q)):
                ispair == 0
            let partners = partners + ispair
        if col_of(p) == col_of(q) and row_of(q) < row_of(p):
            let mid = 0
            for s in col(col_of(p)):
                if row_of(q) < row_of(s) and row_of(s) < row_of(p):
                    let mid = mid + b2i(at(a, s) != 8)
            let ispair = b2i(at(a, q) == DOWN and at(a, p) == UP and mid == 0)
            if regions_share_border(region_id(p), region_id(q)):
                ispair == 0
            let partners = partners + ispair
    at(a, p) != 8 => partners == 1
    at(a, p) == 8 => partners == 0
