# 回路经过所有圆圈。圈中数字 = 穿过该圈的直线段长度。
import "loops"

def geradeweg(e, o, n):
    cloop(e)
    for p in clue_cells(o):
        on_loop(e, p)
    for p in clue_cells(n):
        on_loop(e, p)
        goes_straight(e, p)
        straight_len_through(e, p) == n[p]

geradeweg(e, o, n)
