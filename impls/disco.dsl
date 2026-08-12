# 每个区域内涂黑恰好两组连通的格子；所有涂黑格连通；无全黑 2x2。
import "shading"

wall_rule(x)

# 「区域内恰好两组」的必要条件：每区域至少两个涂黑格。
for reg in regions:
    num_eq(x[reg], 1) >= 2
