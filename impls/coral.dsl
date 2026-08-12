# 涂黑格连通、无全黑 2x2；留白格连通到盘面边界；
# 盘面外的数字表示此行/此列中每段连续涂黑格的长度（无顺序要求）。
import "shading"

wall_rule(x)
# 留白必须能连到边界（注意是留白，不是涂黑）。
group_touches_border(x, 0)
