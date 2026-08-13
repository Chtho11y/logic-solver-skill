# 涂黑格连通、无全黑 2x2；
# 盘面外的数字依次表示此行/此列中每一段连续涂黑格的长度。
# 问号（-1）已编码；星号（任意段数）未编码。
import "shading"
import "outside"

wall_rule(x)
row_runs(x, "left")
col_runs(x, "top")
