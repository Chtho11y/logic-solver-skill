# 黑格孤立；其余划分成 1x2（骨牌可以相邻）。数字格不涂黑。
# 横骨牌上的数字 = 该行黑格数；竖骨牌上的数字 = 该列黑格数。
import "regions"
import "shading"

no_adjacent(x, 1)
clue_cells_white(x, n)

for p in cells():
    x[p] == 1 => c.size[p] == 1
    x[p] == 0 => c.size[p] == 2

for p in clue_cells(n):
    let horiz = false
    let left = shift(p, 0, -1)
    let right = shift(p, 0, 1)
    if left.size == 1:
        let horiz = horiz or (c[p] == c[left])
    if right.size == 1:
        let horiz = horiz or (c[p] == c[right])
    n[p] == ite(horiz, num_eq(x[row(row_of(p))], 1), num_eq(x[col(col_of(p))], 1))
