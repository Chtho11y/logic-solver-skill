# doubleback — 二次返回
# 回路经过所有格子中心且不自交；回路必须经过每个区域恰好两次。

import "loops"
import "regions"

full_loop(e)

for reg in regions:
    region_crossings(e, reg) == 4
