# 每个区域内涂黑恰好两组连通的格子；所有涂黑格连通；无全黑 2x2。
import "shading"

wall_rule(x)

for reg in regions:
    cc_count_in(x, 1, reg) == 2
