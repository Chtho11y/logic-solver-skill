# 每一组涂黑的连通组都是正方形；在每行/每列内，任意两个仅由留白格分隔的涂黑格
# 不能在两个全等的正方形里；数字 = 此格及与其相邻的（至多）四格中涂黑格的个数。
import "shading"

is_rect_group(x, 1)
around_black_clue(x, n)
