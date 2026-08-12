# detour — 绕道
# 回路经过所有格子中心且不自交；数字表示回路在此区域内转弯的次数。

import "loops"
import "regions"

full_loop(e)

for p in clue_cells(n):
    region_turns(e, region_of(p)) == at(n, p)
