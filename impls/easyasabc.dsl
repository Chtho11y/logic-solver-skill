# 每行每列字母 1..k 各一次，其余留空；盘外字母是该方向看到的第一个字母。
import "fill"
import "outside"

def easyasabc(x):
    let k = param("k")
    subset_latin(x, k)
    outside_first_letter(x)

easyasabc(x)
