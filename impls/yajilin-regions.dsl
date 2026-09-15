# 回路经过所有未涂黑格；黑格不相邻；数字 = 该区域黑格数。
import "loops"
import "shading"

def yajilin_regions(e, x, n):
    loop_visits_all_but(e, x)
    no_adjacent(x, 1)
    region_black_count(x, n)

yajilin_regions(e, x, n)
