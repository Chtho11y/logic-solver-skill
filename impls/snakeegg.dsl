# 涂黑一条宽度为一的蛇；黑圈表示此格是蛇的一端；
# 数字 = 其所在的留白连通组格数。
import "shading"

snake_shape(x, 1)
group_size_clue(x, n)

for p in clue_cells(o):
    is_black(x, p)
    n_adj4(x, p, 1) == 1

if has_param("eggs"):
    let eggs = param("eggs")
    if eggs.size > 0:
        let sz = cc_size(x)
        let items = []
        for p in cells():
            let items = items and [ite(is_white(x, p) and cc_root(x, p), at(sz, p), 0)]
        values_set(items, eggs)
