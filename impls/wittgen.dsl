# 放置一些互不重叠的 1x3 长方形（桌子）；桌子不能覆盖数字格；
# 数字 = 与之相邻的（至多）四格中被桌子覆盖的格数；所有未被覆盖的格子连通。
import "shading"

groups_of_size(x, 1, 3)
width_one(x, 1)
clue_cells_white(x, n)
adj_black_clue(x, n)
connected(x, 0)
