# mochikoro — 藕断丝连
# 无全黑 2x2；所有留白格对角连通成一个整体；每组留白格是长方形；
# 每组留白格至多含一个数字，数字表示该组的面积。

import "shading"

no_black_2x2(x)
cc8_count(x, 0) <= 1
is_rect_group(x, 0)

let sz = cc_size(x)
for p in clue_cells(n):
    is_white(x, p)
    at(sz, p) == at(n, p)

clues_in_distinct_groups(x, n)
