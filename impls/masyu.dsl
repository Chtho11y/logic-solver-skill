# masyu — 珍珠
# 画一条经过格子中心且不自交的回路，并通过所有带圈的格子。
# 白圈：直行，且前后两格中至少一格转弯。黑圈：转弯，且前后两格均直行。

import "loops"

cloop(e)

for p in clue_cells(o):
    on_loop(e, p)
    if at(o, p) == 1:
        goes_straight(e, p)
        white_pearl(e, p)
    else:
        turns(e, p)
        black_pearl(e, p)

def white_pearl(e, p):
    goes_horizontal(e, p) => turn_beside(e, p, LEFT) or turn_beside(e, p, RIGHT)
    goes_vertical(e, p) => turn_beside(e, p, UP) or turn_beside(e, p, DOWN)

def black_pearl(e, p):
    for d in [UP, DOWN, LEFT, RIGHT]:
        link_dir(e, p, d) == 1 => straight_beside(e, p, d)
