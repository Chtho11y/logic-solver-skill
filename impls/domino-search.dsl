# 分成 1x2；盘面数字给定，每种无序数对至多出现在一个骨牌上。
import "regions"

all_regions_size(c, 2)
for p in cells():
    for q in adj4(p):
        if before(p, q):
            for p2 in cells():
                for q2 in adj4(p2):
                    if before(p2, q2):
                        if before(p, p2) or (row_of(p) == row_of(p2) and col_of(p) == col_of(p2) and before(q, q2)):
                            if same_pair(p, q, p2, q2):
                                not (at(c, p) == at(c, q) and at(c, p2) == at(c, q2))

def same_pair(p, q, p2, q2):
    if at(n, p) == at(n, p2):
        if at(n, q) == at(n, q2):
            return true
    if at(n, p) == at(n, q2):
        if at(n, q) == at(n, p2):
            return true
    return false
