# 涂黑格连通、无全黑 2x2；留白格连通到盘面边界；
# 盘面外的数字表示此行/此列中每段连续涂黑格的长度（无顺序要求）。
import "shading"
import "outside"

wall_rule(x)
group_touches_border(x, 0)
row_runs_set(x, "left")
row_runs_set(x, "right")
col_runs_set(x, "top")
col_runs_set(x, "bottom")
