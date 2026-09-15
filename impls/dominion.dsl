# 涂黑一些 1x2 的长方形（互不相邻），把盘面分为若干留白区域；字母格不能涂黑；
# 每个区域有且仅有一种字母，相同的字母都在同一个区域。
import "shading"

def dominion(x, a):
    all_dominoes(x, 1)
    clue_cells_white(x, a)

    # 相同字母必须同区域，不同字母必须不同区域。
    let ids = cc_id(x)
    for p in clue_cells(a):
        for q in clue_cells(a):
            if before(p, q):
                if a[p] == a[q]:
                    ids[p] == ids[q]
                else:
                    ids[p] != ids[q]

dominion(x, a)
