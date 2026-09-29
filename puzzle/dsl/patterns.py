"""Small finite clue patterns, independent of the constraint backend."""
from collections import Counter
from functools import lru_cache


@lru_cache(maxsize=512)
def cyclic_run_masks(size: int, lengths: tuple[int, ...], cyclic: bool = True) -> tuple[int, ...]:
    if not 1 <= size <= 12:
        raise ValueError("cyclic_runs requires 1 to 12 positions")
    if not lengths or any(n < -1 or n > size for n in lengths):
        raise ValueError("cyclic_runs requires nonempty lengths in -1..size")
    if 0 in lengths and lengths != (0,):
        raise ValueError("zero must be the only cyclic run clue")
    required = Counter(n for n in lengths if n != -1)
    accepted = []
    for mask in range(1 << size):
        if mask == 0:
            valid = lengths in ((0,), (-1,))
        else:
            bits = [(mask >> i) & 1 for i in range(size)]
            if not cyclic:
                runs, run = [], 0
                for bit in bits + [0]:
                    if bit:
                        run += 1
                    elif run:
                        runs.append(run)
                        run = 0
            elif all(bits):
                runs = [size]
            else:
                start = bits.index(0)
                runs, run = [], 0
                for step in range(1, size + 1):
                    if bits[(start + step) % size]:
                        run += 1
                    elif run:
                        runs.append(run)
                        run = 0
            actual = Counter(runs)
            valid = len(runs) == len(lengths) and not (required - actual)
        if valid:
            accepted.append(mask)
    return tuple(accepted)
