# 无全黑/全白 2x2；每个区域要么全部涂黑要么全部留白；
# 所有留白格连通且不成环（任两留白格之间存在唯一简单路径）；
# 圆圈在 S 到 G 的唯一路径上，三角形不在。
import "shading"
import "regions"

no_mono_2x2(x)
region_uniform(x)
# 连通且无环 ⟺ 树 ⟺ 任两格之间路径唯一。
color_is_tree(x, 0)
