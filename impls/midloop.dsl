# 回路笔直经过每个黑点，且黑点是该直线段的中点。
import "loops"

def midloop(e, o):
    cloop(e)
    for p in clue_cells(o):
        on_loop(e, p)
        goes_straight(e, p)
        used_arm_len(e, p, LEFT) == used_arm_len(e, p, RIGHT)
        used_arm_len(e, p, UP) == used_arm_len(e, p, DOWN)

midloop(e, o)
