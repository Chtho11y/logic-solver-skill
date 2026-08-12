# 留白格连通且无全白 2x2；点提示相邻四格黑白多寡；
# 白色三角形格必须留白且恰和三个留白格相邻；其余留白格恰和两个留白格相邻。
import "shading"

connected(x, 0)
no2x2(x, 0)
majority_dot_clue(x, t)

for p in cells():
    if has_value(v, p):
        is_white(x, p)
        n_adj4(x, p, 0) == 3
    else:
        is_white(x, p) => n_adj4(x, p, 0) == 2
