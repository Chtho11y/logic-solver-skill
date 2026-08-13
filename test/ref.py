"""Independent reference checkers for the fully-implemented shading rules.

Each ``check_<rule>(board, inst)`` is a pure-Python implementation of the
puzzle's rule (as described in ``rules.txt``) that does NOT share any code with
the DSL solver.  The test suite uses it to validate that whatever the z3-based
solver produces really satisfies the rule — catching under- and over-encoded
constraints.

    board : dict {(r, c): 0|1}      the solved shading (1 = black)
    inst  : dict with rows/cols/clues/regions/params (the instance JSON)
"""

from __future__ import annotations

from collections import deque


def _n4(board, rows, cols, r, c):
    out = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            out.append((nr, nc))
    return out


def _n8(board, rows, cols, r, c):
    out = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                out.append((nr, nc))
    return out


def _components(board, rows, cols, value):
    seen = set()
    comps = []
    for r in range(rows):
        for c in range(cols):
            if board[(r, c)] == value and (r, c) not in seen:
                q = deque([(r, c)])
                seen.add((r, c))
                comp = []
                while q:
                    p = q.popleft()
                    comp.append(p)
                    for nb in _n4(board, rows, cols, *p):
                        if nb not in seen and board[nb] == value:
                            seen.add(nb)
                            q.append(nb)
                comps.append(comp)
    return comps


def _count_comps(board, rows, cols, value):
    return len(_components(board, rows, cols, value))


def _region(inst, r, c):
    regions = inst.get("regions", {})
    return regions.get(f"{r},{c}")


# ---------------------------------------------------------------------------
# shared rule skeletons (mirror the DSL's shading/regions helpers)
# ---------------------------------------------------------------------------


def _blacks_isolated(board, rows, cols):
    for p, v in board.items():
        if v == 1:
            for nb in _n4(board, rows, cols, *p):
                if board[nb] == 1:
                    return f"blacks adjacent at {p} and {nb}"
    return None


def _whites_connected(board, rows, cols):
    if _count_comps(board, rows, cols, 0) > 1:
        return "whites not connected"
    return None


def _island_rule(board, rows, cols):
    return _blacks_isolated(board, rows, cols) or _whites_connected(board, rows, cols)


def _no_white_2x2(board, rows, cols):
    for r in range(rows - 1):
        for c in range(cols - 1):
            if all(board[(r + dr, c + dc)] == 0 for dr in (0, 1) for dc in (0, 1)):
                return f"all-white 2x2 at ({r},{c})"
    return None


def _no_black_2x2(board, rows, cols):
    for r in range(rows - 1):
        for c in range(cols - 1):
            if all(board[(r + dr, c + dc)] == 1 for dr in (0, 1) for dc in (0, 1)):
                return f"all-black 2x2 at ({r},{c})"
    return None


def _no_white_crossing_3_regions(board, rows, cols, inst):
    """A maximal white horizontal/vertical run may touch at most 2 regions."""
    for r in range(rows):
        c = 0
        while c < cols:
            if board[(r, c)] == 1:
                c += 1
                continue
            end = c
            while end < cols and board[(r, end)] == 0:
                end += 1
            seen = {_region(inst, r, k) for k in range(c, end)}
            if len(seen) > 2:
                return f"white row segment rows={r} cols={c}..{end - 1} crosses too many regions"
            c = end
    for c in range(cols):
        r = 0
        while r < rows:
            if board[(r, c)] == 1:
                r += 1
                continue
            end = r
            while end < rows and board[(end, c)] == 0:
                end += 1
            seen = {_region(inst, k, c) for k in range(r, end)}
            if len(seen) > 2:
                return f"white col segment col={c} rows={r}..{end - 1} crosses too many regions"
            r = end
    return None


def _black_count_region(board, inst, r, c):
    rid = _region(inst, r, c)
    total = 0
    for key, rid2 in inst.get("regions", {}).items():
        if rid2 == rid:
            rr, cc = map(int, key.split(","))
            total += board[(rr, cc)]
    return total


# ---------------------------------------------------------------------------
# per-rule checkers
# ---------------------------------------------------------------------------


def check_nothree(board, inst):
    rows, cols = inst["rows"], inst["cols"]
    err = _island_rule(board, rows, cols)
    if err:
        return [err]

    for key, val in inst["clues"].get("o", {}).items():
        if val is None:
            continue
        r, c = map(int, key.split(","))
        n = sum(1 for nb in _n8(board, rows, cols, r, c) if board[nb] == 1)
        if n != 1:
            return [f"circle at ({r},{c}) touches {n} blacks (need 1)"]

    # no three equally spaced blacks in a row or column
    for r in range(rows):
        cols_b = [c for c in range(cols) if board[(r, c)] == 1]
        for i in range(len(cols_b)):
            for j in range(i + 1, len(cols_b)):
                c1, c2 = cols_b[i], cols_b[j]
                c3 = 2 * c2 - c1
                if 0 <= c3 < cols and board[(r, c3)] == 1:
                    return [f"equally spaced black triple in row {r}: cols {c1},{c2},{c3}"]
    for c in range(cols):
        rows_b = [r for r in range(rows) if board[(r, c)] == 1]
        for i in range(len(rows_b)):
            for j in range(i + 1, len(rows_b)):
                r1, r2 = rows_b[i], rows_b[j]
                r3 = 2 * r2 - r1
                if 0 <= r3 < rows and board[(r3, c)] == 1:
                    return [f"equally spaced black triple in col {c}: rows {r1},{r2},{r3}"]
    return []


def check_sumiwake(board, inst):
    rows, cols = inst["rows"], inst["cols"]
    err = _island_rule(board, rows, cols)
    if err:
        return [err]
    err = _no_white_crossing_3_regions(board, rows, cols, inst)
    if err:
        return [err]
    for key, val in inst["clues"].get("o", {}).items():
        if val is None:
            continue
        r, c = map(int, key.split(","))
        n = sum(1 for nb in _n8(board, rows, cols, r, c) if board[nb] == 1)
        want = 1 if val == 1 else 2
        if n != want:
            return [f"circle at ({r},{c}) touches {n} blacks (need {want})"]
    return []


def check_usoone(board, inst):
    rows, cols = inst["rows"], inst["cols"]
    err = _island_rule(board, rows, cols)
    if err:
        return [err]
    clues = inst["clues"].get("n", {})
    for key, val in clues.items():
        if val is None:
            continue
        r, c = map(int, key.split(","))
        if board[(r, c)] == 1:
            return [f"clue cell ({r},{c}) is black"]
    # The printed numbers may be lies: each region has EXACTLY ONE wrong clue.
    regions = inst.get("regions", {})
    by_region = {}
    for key, val in clues.items():
        if val is None:
            continue
        r, c = map(int, key.split(","))
        rid = regions.get(key)
        by_region.setdefault(rid, []).append((r, c))
    for rid, cells in by_region.items():
        wrong = 0
        for r, c in cells:
            n = sum(1 for nb in _n4(board, rows, cols, r, c) if board[nb] == 1)
            if n != clues[f"{r},{c}"]:
                wrong += 1
        if wrong != 1:
            return [f"region {rid} has {wrong} wrong clues (need 1)"]
    return []


_DIR = {0: (-1, 0), 1: (1, 0), 2: (0, -1), 3: (0, 1)}


def check_yajikazu(board, inst):
    rows, cols = inst["rows"], inst["cols"]
    err = _island_rule(board, rows, cols)
    if err:
        return [err]
    ns = inst["clues"].get("n", {})
    ds = inst["clues"].get("d", {})
    for key, val in ns.items():
        if val is None or key not in ds or ds[key] is None:
            continue
        r, c = map(int, key.split(","))
        if board[(r, c)] == 1:
            continue  # clue on a black cell gives no information
        dr, dc = _DIR[ds[key]]
        rr, cc = r + dr, c + dc
        n = 0
        while 0 <= rr < rows and 0 <= cc < cols:
            n += board[(rr, cc)]
            rr, cc = rr + dr, cc + dc
        if n != val:
            return [f"arrow at ({r},{c}) counts {n} blacks in direction {ds[key]}, clue says {val}"]
    return []


def check_ayeheya(board, inst):
    rows, cols = inst["rows"], inst["cols"]
    err = _island_rule(board, rows, cols)
    if err:
        return [err]
    err = _no_white_crossing_3_regions(board, rows, cols, inst)
    if err:
        return [err]
    for key, val in inst["clues"].get("n", {}).items():
        if val is None:
            continue
        r, c = map(int, key.split(","))
        if _black_count_region(board, inst, r, c) != val:
            return [f"region of ({r},{c}) has {_black_count_region(board, inst, r, c)} blacks, clue {val}"]

    # every region's black pattern is 180 degree rotation symmetric
    regions = {}
    for key, rid in inst.get("regions", {}).items():
        r, c = map(int, key.split(","))
        regions.setdefault(rid, []).append((r, c))
    for rid, cells in regions.items():
        minr = min(p[0] for p in cells)
        maxr = max(p[0] for p in cells)
        minc = min(p[1] for p in cells)
        maxc = max(p[1] for p in cells)
        for r, c in cells:
            mr = minr + maxr - r
            mc = minc + maxc - c
            if board[(r, c)] != board[(mr, mc)]:
                return [f"region {rid} not 180-symmetric: ({r},{c}) != ({mr},{mc})"]
    return []


def check_bosnianroad(board, inst):
    rows, cols = inst["rows"], inst["cols"]
    # blacks form a single closed ring: connected, degree-2, no 2x2
    if _count_comps(board, rows, cols, 1) != 1:
        return ["blacks not connected into one ring"]
    err = _no_black_2x2(board, rows, cols)
    if err:
        return [err]
    for p, v in board.items():
        if v == 1:
            if sum(1 for nb in _n4(board, rows, cols, *p) if board[nb] == 1) != 2:
                return [f"black {p} has degree != 2 in ring"]
    for key, val in inst["clues"].get("n", {}).items():
        if val is None:
            continue
        r, c = map(int, key.split(","))
        if board[(r, c)] == 1:
            return [f"clue cell ({r},{c}) is black"]
        n = sum(1 for nb in _n8(board, rows, cols, r, c) if board[nb] == 1)
        if n != val:
            return [f"clue at ({r},{c}) = {val} but 8-neighbour black count = {n}"]
    return []


def check_sansaroad(board, inst):
    rows, cols = inst["rows"], inst["cols"]
    if _count_comps(board, rows, cols, 0) != 1:
        return ["whites not connected"]
    err = _no_white_2x2(board, rows, cols)
    if err:
        return [err]
    # dot clues on 4-neighbourhood majority
    for key, val in inst["clues"].get("t", {}).items():
        if val is None:
            continue
        r, c = map(int, key.split(","))
        ws = sum(1 for nb in _n4(board, rows, cols, r, c) if board[nb] == 0)
        bs = sum(1 for nb in _n4(board, rows, cols, r, c) if board[nb] == 1)
        ok = (val == 1 and ws > bs) or (val == 2 and bs > ws) or (val == 3 and ws == bs)
        if not ok:
            return [f"dot at ({r},{c}) value {val} but w={ws} b={bs}"]
    tris = set()
    for key, val in inst["clues"].get("v", {}).items():
        if val is None:
            continue
        tris.add(tuple(map(int, key.split(","))))
    for r in range(rows):
        for c in range(cols):
            if board[(r, c)] == 0:
                deg = sum(1 for nb in _n4(board, rows, cols, r, c) if board[nb] == 0)
                if (r, c) in tris:
                    if deg != 3:
                        return [f"triangle cell ({r},{c}) has {deg} white neighbours (need 3)"]
                elif deg != 2:
                    return [f"white cell ({r},{c}) has {deg} white neighbours (need 2)"]
            else:
                if (r, c) in tris:
                    return [f"triangle cell ({r},{c}) is black"]
    return []


def check_dominion(board, inst):
    rows, cols = inst["rows"], inst["cols"]
    # blacks pair into non-touching 1x2 dominoes
    for p, v in board.items():
        if v == 1:
            if sum(1 for nb in _n4(board, rows, cols, *p) if board[nb] == 1) != 1:
                return [f"black {p} not part of a 1x2 domino"]
    clues = inst["clues"].get("a", {})
    for key, val in clues.items():
        if val is None:
            continue
        r, c = map(int, key.split(","))
        if board[(r, c)] == 1:
            return [f"letter cell ({r},{c}) is black"]
    # same letters share a white region; different letters do not
    comps = _components(board, rows, cols, 0)
    comp_of = {}
    for ci, comp in enumerate(comps):
        for p in comp:
            comp_of[p] = ci
    by_letter = {}
    for key, val in clues.items():
        if val is None:
            continue
        r, c = map(int, key.split(","))
        by_letter.setdefault(val, set()).add(comp_of[(r, c)])
    for letter, comps_set in by_letter.items():
        if len(comps_set) > 1:
            return [f"letter {letter} appears in multiple white regions"]
    letters = list(by_letter)
    for i in range(len(letters)):
        for j in range(i + 1, len(letters)):
            if by_letter[letters[i]] == by_letter[letters[j]]:
                return [f"letters {letters[i]} and {letters[j]} share a region"]
    return []


def check_norinuri(board, inst):
    rows, cols = inst["rows"], inst["cols"]
    for p, v in board.items():
        if v == 1:
            if sum(1 for nb in _n4(board, rows, cols, *p) if board[nb] == 1) != 1:
                return [f"black {p} not part of a 1x2 domino"]
    clues = inst["clues"].get("n", {})
    for key, val in clues.items():
        if val is None:
            continue
        r, c = map(int, key.split(","))
        if board[(r, c)] == 1:
            return [f"clue cell ({r},{c}) is black"]
    comps = _components(board, rows, cols, 0)
    comp_of = {}
    sizes = {}
    for ci, comp in enumerate(comps):
        sizes[ci] = len(comp)
        for p in comp:
            comp_of[p] = ci
    per_comp = {}
    for key, val in clues.items():
        if val is None:
            continue
        r, c = map(int, key.split(","))
        per_comp.setdefault(comp_of[(r, c)], []).append(val)
    for ci, vals in per_comp.items():
        if len(vals) != 1:
            return [f"white region {ci} has {len(vals)} clues (need 1)"]
        if vals[0] != sizes[ci]:
            return [f"white region {ci} size {sizes[ci]} but clue {vals[0]}"]
    if len(per_comp) != len(comps):
        return [f"{len(comps)} white regions but {len(per_comp)} have clues"]
    return []


def check_isowatari(board, inst):
    rows, cols = inst["rows"], inst["cols"]
    n = inst.get("params", {}).get("n")
    if _count_comps(board, rows, cols, 0) != 1:
        return ["whites not connected"]
    err = _no_white_2x2(board, rows, cols)
    if err:
        return [err]
    if n is not None:
        comps = _components(board, rows, cols, 1)
        for comp in comps:
            if len(comp) != n:
                return [f"black group {comp} has size {len(comp)}, need {n}"]
    for key, val in inst["clues"].get("o", {}).items():
        if val is None:
            continue
        r, c = map(int, key.split(","))
        if val == 2 and board[(r, c)] != 1:
            return [f"black circle ({r},{c}) is white"]
        if val == 1 and board[(r, c)] != 0:
            return [f"white circle ({r},{c}) is black"]
    return []


def check_aquarium(board, inst):
    rows, cols = inst["rows"], inst["cols"]
    regions = inst.get("regions", {})
    # water sinks: black cell forces black directly below within same region
    for r in range(rows - 1):
        for c in range(cols):
            if regions.get(f"{r},{c}") is not None and regions.get(f"{r},{c}") == regions.get(f"{r + 1},{c}"):
                if board[(r, c)] == 1 and board[(r + 1, c)] == 0:
                    return [f"water unstable at ({r},{c}): black above white ({r+1},{c}) in same region"]
    # flat surface: same-region horizontal neighbours are equal
    for r in range(rows):
        for c in range(cols - 1):
            if regions.get(f"{r},{c}") is not None and regions.get(f"{r},{c}") == regions.get(f"{r},{c + 1}"):
                if board[(r, c)] != board[(r, c + 1)]:
                    return [f"uneven surface at ({r},{c}) vs ({r},{c + 1}) in same region"]
    # row / column counts
    left = inst.get("params", {}).get("left")
    if left:
        for r, want in enumerate(left):
            if want is None or want < 0:
                continue
            got = sum(1 for c in range(cols) if board[(r, c)] == 1)
            if got != want:
                return [f"row {r} has {got} blacks, clue {want}"]
    top = inst.get("params", {}).get("top")
    if top:
        for c, want in enumerate(top):
            if want is None or want < 0:
                continue
            got = sum(1 for r in range(rows) if board[(r, c)] == 1)
            if got != want:
                return [f"col {c} has {got} blacks, clue {want}"]
    return []


CHECKERS = {
    "nothree": check_nothree,
    "sumiwake": check_sumiwake,
    "usoone": check_usoone,
    "yajikazu": check_yajikazu,
    "ayeheya": check_ayeheya,
    "bosnianroad": check_bosnianroad,
    "sansaroad": check_sansaroad,
    "dominion": check_dominion,
    "norinuri": check_norinuri,
    "isowatari": check_isowatari,
    "aquarium": check_aquarium,
}
