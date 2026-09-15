# 每个正整数等于自身与正交邻格之差的绝对值之和（缺邻视为 0）。
import "core"

for p in cells():
    let s = 0
    for q in adj4(p):
        let s = s + abs(at(x, p) - at(x, q))
    at(x, p) == s
