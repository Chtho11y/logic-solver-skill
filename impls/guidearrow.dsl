# 涂黑格互不相邻、留白连通；留白格不能形成回路（含 2x2）；
# 箭头表示从此格出发不经涂黑格、不倒退走到星星的唯一方向。
import "shading"

blacks_isolated(x)
# 留白连通且无环（这同时排除了全白 2x2）。
color_is_tree(x, 0)
