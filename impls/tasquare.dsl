# 每一组涂黑的连通组都是正方形；留白格连通；
# 白色正方形格必须留白，且需和至少一个涂黑正方形相邻；
# 数字 = 与之相邻的所有涂黑正方形的面积之和。
import "shading"

square_groups(x, 1)
connected(x, 0)
clue_cells_white(x, n)

for p in clue_cells(n):
    n_adj4(x, p, 1) >= 1
    adj_square_area(x, p) == at(n, p)

def adj_square_area(x, p):
    let ids = cc_id(x)
    let sz = cc_size(x)
    let total = 0
    for q in cells():
        let touch = false
        for a in adj4(p):
            let touch = touch or (is_black(x, a) and at(ids, a) == at(ids, q))
        let total = total + ite(cc_root(x, q) and is_black(x, q) and touch, at(sz, q), 0)
    return total
