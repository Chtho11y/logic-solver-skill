# 每个区域 1..N；正交相邻不同；同一区域里上方必须比下方大。
import "fill"

def cojun(x):
    region_1_to_n(x)
    adjacent_differ(x)
    for p in cells():
        let q = shift(p, 1, 0)
        if q.size == 1:
            if same_region(p, q):
                x[p] > x[q]

cojun(x)
