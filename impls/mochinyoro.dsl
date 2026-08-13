# 无全黑 2x2；所有留白格对角连通；每一组连通的留白格必须是长方形；
# 每一组连通的留白格至多包含一个数字；数字 = 其所在留白连通组的格数；
# 任意一组连通的涂黑格都不能是长方形。
import "shading"

no2x2(x, 1)
connected8(x, 0)
is_rect_group(x, 0)
group_size_clue(x, n)
clues_in_distinct_groups(x, n)

for p in cells():
    is_black(x, p) => not cc_is_rect(x, p)
