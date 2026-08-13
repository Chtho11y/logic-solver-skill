# domino-search — 多米诺搜寻
# 分成两格区域。param("tiles") 中数字组成的每个无序数对恰好出现在一个区域内。

import "regions"

all_regions_size(c, 2)

if has_param("tiles"):
    for a in param("tiles"):
        for b in param("tiles"):
            if a <= b:
                let cnt = 0
                for p in cells():
                    for q in adj4(p):
                        if before(p, q):
                            let match = (at(n, p) == a and at(n, q) == b) or (at(n, p) == b and at(n, q) == a)
                            let cnt = cnt + b2i(at(c, p) == at(c, q) and match)
                cnt == 1
