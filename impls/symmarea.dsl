# Fillomino：相邻区域面积不同，数字 = 面积；每个区域 180° 旋转对称。
import "regions"

def symmarea(c, n):
    neighbour_sizes_differ(c)
    region_size_clue(c, n)
    region_180_symmetric(c)

symmarea(c, n)
