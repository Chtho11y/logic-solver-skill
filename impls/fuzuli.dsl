# 每行每列 1..k 各一次，其余留空；无 2x2 全填；叉号格必须留空。
import "fill"

def fuzuli(x, m):
    let k = param("k")
    subset_latin(x, k)
    for w in slide(2, 2):
        let filled = 0
        for p in w:
            let filled = filled + b2i(x[p] != 0)
        filled < 4
    for p in clue_cells(m):
        x[p] == 0

fuzuli(x, m)
