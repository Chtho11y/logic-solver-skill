# 每行每列 1..k 各一次（k=N 时即拉丁方）；盘外数字 = 该方向可见的摩天楼数。
# 0 表示空地，不遮挡视线。
import "fill"
import "outside"

def skyscrapers(x):
    let k = param("k")
    subset_latin(x, k)
    outside_visible(x)

skyscrapers(x)
