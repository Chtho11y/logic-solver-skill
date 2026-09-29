import "shading"

def room_shade(x, n):
    island_rule(x)
    for reg in regions:
        num_eq(x[reg], 1) == param("k")
    clue_cells_white(x, n)
    adj_black_clue(x, n)

room_shade(x, n)
