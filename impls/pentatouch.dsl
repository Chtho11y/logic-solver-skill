# pentatouch — pentatouch
# 放置若干五格骨牌。不同形状仅在被标记的格点上对角相邻。
# 形状目录未编码（任意五格骨牌）。

import "shading"
import "place2"

groups_of_size(x, 1, 5)
cc_count(x, 1) >= 1
let ids = cc_id(x)

for v in corners():
    if has_value(o, v):
        vertex_diag_kiss(x, ids, v)
    else:
        not vertex_diag_kiss(x, ids, v)
