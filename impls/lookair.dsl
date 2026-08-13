# 每一组涂黑的连通组都是正方形；在每行/每列内，任意两个仅由留白格分隔的涂黑格
# 不能在两个全等的正方形里；数字 = 此格及与其相邻的（至多）四格中涂黑格的个数。
import "shading"

square_groups(x, 1)
around_black_clue(x, n)

let sz = cc_size(x)
for p in cells():
    for q in cells():
        if row_of(p) == row_of(q) and col_of(p) + 1 < col_of(q):
            let clear = true
            for k in row(row_of(p)):
                if col_of(p) < col_of(k) and col_of(k) < col_of(q):
                    let clear = clear and is_white(x, k)
            is_black(x, p) and is_black(x, q) and clear => at(sz, p) != at(sz, q)
        if col_of(p) == col_of(q) and row_of(p) + 1 < row_of(q):
            let clear = true
            for k in col(col_of(p)):
                if row_of(p) < row_of(k) and row_of(k) < row_of(q):
                    let clear = clear and is_white(x, k)
            is_black(x, p) and is_black(x, q) and clear => at(sz, p) != at(sz, q)
