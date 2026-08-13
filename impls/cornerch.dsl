# 涂黑一些空格，使所有留白格对角连通；数字格不能涂黑；
# 数字 = 其所在留白连通组的面积；面积为偶数则必须是长方形，为奇数则不能是长方形。
import "shading"

connected8(x, 0)
clue_cells_white(x, n)
group_size_clue(x, n)

let sz = cc_size(x)
for p in cells():
    is_white(x, p) and at(sz, p) % 2 == 0 => cc_is_rect(x, p)
    is_white(x, p) and at(sz, p) % 2 == 1 => not cc_is_rect(x, p)
