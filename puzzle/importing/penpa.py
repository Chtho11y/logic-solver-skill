"""Decode a Penpa+ share URL into a :class:`LayerBoard`.

Penpa+ stores the editor state as zlib-raw + Base64 JSON. The payload is a
generic drawing: Surface / Number / Symbol / Line / LineE, not a typed
puzzle. Coordinates use a 1-D index on a grid padded by 2 cells on every
side (plus optional "space" bands for outside clues).

See https://github.com/swaroopg92/penpa-edit ``docs/js/general.js``
(``encrypt_data`` / ``decrypt_data`` / ``load``).
"""

from __future__ import annotations

import json
import zlib
from base64 import b64decode, b64encode
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlsplit

from .board import LayerBoard, regions_from_walls
from .errors import PuzzleImportError
from .pids import guess_from_tags

# Applied on encode in this order; decode reverses it. First pair escapes "z".
# Copied from Penpa+ / puzzlekit COMPRESS_SUB.
COMPRESS_SUB: tuple[tuple[str, str], ...] = (
    ("z", "zZ"),
    ('"qa"', "z9"),
    ('"pu_q"', "zQ"),
    ('"pu_a"', "zA"),
    ('"grid"', "zG"),
    ('"edit_mode"', "zM"),
    ('"surface"', "zS"),
    ('"line"', "zL"),
    ('"lineE"', "zE"),
    ('"wall"', "zW"),
    ('"cage"', "zC"),
    ('"number"', "zN"),
    ('"symbol"', "zY"),
    ('"special"', "zP"),
    ('"board"', "zB"),
    ('"command_redo"', "zR"),
    ('"command_undo"', "zU"),
    ('"command_replay"', "z8"),
    ('"numberS"', "z1"),
    ('"freeline"', "zF"),
    ('"freelineE"', "z2"),
    ('"thermo"', "zT"),
    ('"arrows"', "z3"),
    ('"direction"', "zD"),
    ('"squareframe"', "z0"),
    ('"polygon"', "z5"),
    ('"deletelineE"', "z4"),
    ('"killercages"', "z6"),
    ('"nobulbthermo"', "z7"),
    ('"__a"', "z_"),
    ("null", "zO"),
)

# Penpa surface colour id -> our shade value. Black (4) and dark grey (1)
# become 1; other tints stay as the penpa id so a binder can still see them.
SURFACE_BLACK = {1, 4}

# Penpa number-submode "2" direction suffix -> our arrow 0-3 (U D L R).
# Penpa: 0=N 1=W 2=E 3=S 4=NW 5=NE 6=SW 7=SE
PENPA_DIR_TO_OURS = {
    "0": 0,
    "3": 1,
    "1": 2,
    "2": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
}

OURS_DIR_TO_PENPA = {v: k for k, v in PENPA_DIR_TO_OURS.items()}


def looks_like_penpa(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    lowered = raw.lower()
    if "penpa" in lowered or "swaroopg92" in lowered:
        return True
    if "#m=" in lowered or raw.startswith("m=") or "&p=" in raw:
        return True
    return False


def parse_penpa_payload(url: str) -> dict[str, str]:
    """Extract ``m`` / ``p`` from a full URL, hash fragment, or raw ``m=&p=``."""

    raw = (url or "").strip()
    if not raw:
        raise PuzzleImportError("empty Penpa URL")
    parsed = urlsplit(raw)
    fragment = (parsed.fragment or "").lstrip("?")
    query = (parsed.query or "").lstrip("?")
    candidate = fragment or query
    if not candidate:
        candidate = raw.split("#", 1)[1] if "#" in raw else raw
        candidate = candidate.lstrip("#").lstrip("?")
    mode = "edit"
    payload = ""
    for token in candidate.split("&"):
        if not token:
            continue
        key, sep, value = token.partition("=")
        if not sep:
            if not payload:
                payload = unquote(key)
            continue
        key, value = unquote(key), unquote(value)
        if key == "m":
            mode = value or mode
        elif key == "p" and not payload:
            payload = value
    if not payload:
        payload = candidate
    if not payload:
        raise PuzzleImportError("Penpa URL has no p= payload")
    return {"mode": mode, "p": payload}


def _inflate(payload: str) -> str:
    data = payload.strip()
    # URL-safe and missing padding both show up in pasted links.
    data = data.replace("-", "+").replace("_", "/")
    pad = (-len(data)) % 4
    if pad:
        data += "=" * pad
    try:
        raw = b64decode(data)
    except Exception as exc:
        raise PuzzleImportError("Penpa payload is not valid Base64") from exc
    try:
        return zlib.decompress(raw, -15).decode("utf-8")
    except Exception as exc:
        raise PuzzleImportError("Penpa payload is not zlib-compressed text") from exc


def _deflate(text: str) -> str:
    compressor = zlib.compressobj(wbits=-15)
    raw = compressor.compress(text.encode("utf-8")) + compressor.flush()
    return b64encode(raw).decode("ascii").rstrip("=")


def _expand(text: str) -> str:
    for original, abbr in reversed(COMPRESS_SUB):
        text = text.replace(abbr, original)
    return text


def _compress(text: str) -> str:
    for original, abbr in COMPRESS_SUB:
        text = text.replace(original, abbr)
    return text


def _loads_maybe(text: str, default: Any) -> Any:
    text = (text or "").strip()
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            return json.loads(_expand(text))
        except json.JSONDecodeError:
            return default


@dataclass
class PenpaGrid:
    """Penpa index ↔ (row, col) conversion for a square grid."""

    inner_rows: int
    inner_cols: int
    top: int
    bottom: int
    left: int
    right: int

    @property
    def header_rows(self) -> int:
        return self.inner_rows + self.top + self.bottom

    @property
    def header_cols(self) -> int:
        return self.inner_cols + self.left + self.right

    @property
    def real_rows(self) -> int:
        return self.header_rows + 4

    @property
    def real_cols(self) -> int:
        return self.header_cols + 4

    def cell_index(self, row: int, col: int) -> int:
        pr = row + 2 + self.top
        pc = col + 2 + self.left
        return pr * self.real_cols + pc

    def decode_index(self, index: int) -> tuple[str, tuple[Any, ...]]:
        """Return ``('cell', (r,c))``, ``('outside', (side, i))``, ``('edge', ...)`` or ``('skip', ())``."""

        area = self.real_rows * self.real_cols
        category, rest = divmod(int(index), area)
        pr, pc = divmod(rest, self.real_cols)
        if category == 0:
            return self._place_cell(pr, pc)
        if category == 2:
            # Horizontal edge centre between (pr-1, pc-2) and (pr-1, pc-1)
            row = pr - 1 - self.top
            col = pc - 2 - self.left
            return "edge", ("V", row, col + 1)
        if category == 3:
            row = pr - 2 - self.top
            col = pc - 1 - self.left
            return "edge", ("H", row + 1, col)
        if category == 1:
            # Vertices / corners on the padded lattice.
            row = pr - 1 - self.top
            col = pc - 1 - self.left
            return "corner", (row, col)
        return "skip", (category, pr, pc)

    def _place_cell(self, pr: int, pc: int) -> tuple[str, tuple[Any, ...]]:
        inner_r0 = 2 + self.top
        inner_c0 = 2 + self.left
        inner_r1 = inner_r0 + self.inner_rows
        inner_c1 = inner_c0 + self.inner_cols
        if inner_r0 <= pr < inner_r1 and inner_c0 <= pc < inner_c1:
            return "cell", (pr - inner_r0, pc - inner_c0)
        # Space-margin bands and the 2-cell padding: treat as outside clues.
        if inner_c0 <= pc < inner_c1:
            col = pc - inner_c0
            if pr < inner_r0:
                return "outside", ("top", col)
            if pr >= inner_r1:
                return "outside", ("bottom", col)
        if inner_r0 <= pr < inner_r1:
            row = pr - inner_r0
            if pc < inner_c0:
                return "outside", ("left", row)
            if pc >= inner_c1:
                return "outside", ("right", row)
        return "skip", (pr, pc)


def decode_penpa(url: str) -> LayerBoard:
    parsed = parse_penpa_payload(url)
    plain = _expand(_inflate(parsed["p"]))
    parts = plain.split("\n")
    if not parts or not parts[0]:
        raise PuzzleImportError("Penpa payload has no header")
    header = parts[0].split(",")
    gridtype = (header[0] or "square").strip()
    if gridtype not in {"square", "sudoku"}:
        raise PuzzleImportError(f"only square Penpa grids are supported, got {gridtype!r}")
    if len(header) < 3:
        raise PuzzleImportError("Penpa header is truncated")

    spaces = _loads_maybe(parts[1] if len(parts) > 1 else "", [0, 0, 0, 0])
    if not isinstance(spaces, list) or len(spaces) < 4:
        spaces = [0, 0, 0, 0]
    top, bottom, left, right = (int(spaces[0]), int(spaces[1]), int(spaces[2]), int(spaces[3]))
    header_cols = int(header[1])
    header_rows = int(header[2])
    inner_rows = header_rows - top - bottom
    inner_cols = header_cols - left - right
    if inner_rows <= 0 or inner_cols <= 0:
        raise PuzzleImportError("Penpa grid size is invalid")

    grid = PenpaGrid(inner_rows, inner_cols, top, bottom, left, right)
    title = ""
    author = ""
    source = ""
    if len(header) > 15:
        title = unquote(header[15]).replace("%2C", ",")
        if title.lower().startswith("title:"):
            title = title[6:].strip()
    if len(header) > 16:
        author = unquote(header[16]).replace("%2C", ",")
        if author.lower().startswith("author:"):
            author = author[7:].strip()
    if len(header) > 17:
        source = unquote(header[17]).replace("%2C", ",")

    tags: list[str] = []
    if len(parts) > 17 and parts[17].strip():
        raw_tags = _loads_maybe(parts[17], [])
        if isinstance(raw_tags, list):
            tags = [str(t) for t in raw_tags if t]

    pu_q = _loads_maybe(parts[3] if len(parts) > 3 else "", {})
    if not isinstance(pu_q, dict):
        pu_q = {}

    board = LayerBoard(
        rows=inner_rows,
        cols=inner_cols,
        title=title,
        author=author,
        source=source,
        tags=tags,
        pid=guess_from_tags(tags, title) or "",
        raw={"mode": parsed["mode"], "header": header[:11], "spaces": spaces, "pu_q_keys": sorted(pu_q)},
    )

    _decode_surface(board, grid, pu_q.get("surface") or {})
    _decode_number(board, grid, pu_q.get("number") or {})
    _decode_symbol(board, grid, pu_q.get("symbol") or {})
    _decode_line_e(board, grid, pu_q.get("lineE") or {})
    _decode_line(board, grid, pu_q.get("line") or {})

    walls = {key for key, mark in board.edges.items() if mark.line}
    if walls:
        board.regions = regions_from_walls(board.rows, board.cols, walls)

    leftover = [
        key
        for key in pu_q
        if pu_q[key]
        and key
        not in {
            "surface",
            "number",
            "symbol",
            "line",
            "lineE",
            "command_redo",
            "command_undo",
            "command_replay",
            "polygon",
            "freeline",
            "freelineE",
            "thermo",
            "arrows",
            "direction",
            "squareframe",
            "killercages",
            "cage",
            "deletelineE",
            "wall",
            "numberS",
            "special",
            "board",
            "nobulbthermo",
        }
    ]
    if leftover:
        board.warnings.append("unmapped Penpa keys: " + ", ".join(sorted(leftover)[:12]))
    for key in ("thermo", "arrows", "killercages", "cage", "wall", "numberS"):
        if pu_q.get(key):
            board.warnings.append(f"Penpa {key} is present but not bound to a solver layer")
    return board


def _ensure_outside(board: LayerBoard, side: str, index: int, value: int) -> None:
    length = board.cols if side in {"top", "bottom"} else board.rows
    arr = board.outside.setdefault(side, [-1] * length)
    while len(arr) < length:
        arr.append(-1)
    if 0 <= index < length:
        arr[index] = value


def _parse_int(text: Any) -> int | None:
    if text is None or text == "":
        return None
    if isinstance(text, int):
        return text
    raw = str(text).strip()
    if raw in {".", "-", "–"}:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _apply_cell(board: LayerBoard, grid: PenpaGrid, index: int) -> tuple[str, tuple[Any, ...]]:
    return grid.decode_index(int(index))


def _decode_surface(board: LayerBoard, grid: PenpaGrid, data: dict) -> None:
    for index, colour in data.items():
        kind, payload = _apply_cell(board, grid, int(index))
        if kind != "cell":
            continue
        row, col = payload
        colour_id = int(colour)
        board.cell(row, col).shade = 1 if colour_id in SURFACE_BLACK else colour_id


def _decode_number(board: LayerBoard, grid: PenpaGrid, data: dict) -> None:
    for index, entry in data.items():
        if not isinstance(entry, (list, tuple)) or not entry:
            continue
        raw, _style, submode = (list(entry) + ["", 1, "1"])[:3]
        kind, payload = _apply_cell(board, grid, int(index))
        text = "" if raw is None else str(raw)
        if submode == "2" or "_" in text:
            number_part, sep, dir_part = text.rpartition("_")
            if not sep:
                number_part, dir_part = text, ""
            arrow = PENPA_DIR_TO_OURS.get(dir_part)
            value = _parse_int(number_part)
            if kind == "cell":
                row, col = payload
                mark = board.cell(row, col)
                if arrow is not None:
                    mark.arrow = arrow
                if value is not None:
                    mark.number = value
                elif number_part:
                    mark.number_text = number_part
            continue
        value = _parse_int(text)
        if kind == "cell":
            row, col = payload
            mark = board.cell(row, col)
            if value is not None:
                mark.number = value
            elif text:
                mark.number_text = text
        elif kind == "outside" and value is not None:
            side, idx = payload
            _ensure_outside(board, side, idx, value)


def _decode_symbol(board: LayerBoard, grid: PenpaGrid, data: dict) -> None:
    for index, entry in data.items():
        if not isinstance(entry, (list, tuple)) or len(entry) < 2:
            continue
        shape_id, family = entry[0], str(entry[1])
        kind, payload = grid.decode_index(int(index))
        family_l = family.lower()
        if kind == "edge":
            orient, row, col = payload
            if not board.in_bounds(row if orient == "V" else row - 1 if row > 0 else 0, col if orient == "H" else col - 1 if col > 0 else 0):
                # Still record if the edge itself is on the lattice.
                pass
            if 0 <= (row if orient == "H" else row) and 0 <= (col if orient == "V" else col):
                if "circle" in family_l or family_l in {"ox_B", "ox_E"}:
                    board.edge(orient, row, col).dot = int(shape_id) if int(shape_id) in {1, 2, 3} else 2
            continue
        if kind != "cell":
            continue
        row, col = payload
        if not board.in_bounds(row, col):
            continue
        mark = board.cell(row, col)
        sid = int(shape_id) if str(shape_id).lstrip("-").isdigit() else 1
        if "circle" in family_l:
            mark.circle = sid if sid in {1, 2, 3} else 1
        elif "square" in family_l:
            mark.square = sid if sid else 1
        elif "tri" in family_l:
            mark.triangle = sid if sid else 1
        elif "star" in family_l:
            mark.star = 1
        elif family_l in {"cross", "ox_B", "ox_E"} and sid in {2, 4, 5, 8}:
            mark.cross = 1
        elif "cross" in family_l:
            mark.cross = 1
        elif "tree" in family_l:
            mark.tree = 1
        elif family_l.startswith("ox"):
            # ox_B: 1=white circle, 2=black circle, 3=X, 4=black X, ...
            if sid in {1, 2}:
                mark.circle = sid
            elif sid in {3, 4, 5}:
                mark.cross = 1
        else:
            mark.extra[family] = sid


def _corners_to_edge(c1: tuple[int, int], c2: tuple[int, int]) -> tuple[str, int, int] | None:
    (r1, c1_), (r2, c2_) = c1, c2
    if r1 == r2 and abs(c1_ - c2_) == 1:
        return "H", r1, min(c1_, c2_)
    if c1_ == c2_ and abs(r1 - r2) == 1:
        return "V", min(r1, r2), c1_
    return None


def _decode_line_e(board: LayerBoard, grid: PenpaGrid, data: dict) -> None:
    for key, value in data.items():
        if "," in str(key):
            left, right = str(key).split(",", 1)
            k1, p1 = grid.decode_index(int(left))
            k2, p2 = grid.decode_index(int(right))
            corners: list[tuple[int, int]] = []
            for kind, payload in ((k1, p1), (k2, p2)):
                if kind == "corner":
                    corners.append(payload)  # type: ignore[arg-type]
                elif kind == "cell":
                    # Some links store cell indices; treat as vertex of that cell's top-left.
                    row, col = payload  # type: ignore[misc]
                    corners.append((row, col))
            if len(corners) != 2:
                continue
            edge = _corners_to_edge(corners[0], corners[1])
            if edge is None:
                continue
            orient, row, col = edge
            board.edge(orient, row, col).line = 1 if int(value) else 1
            continue
        if str(key).isdigit():
            kind, payload = grid.decode_index(int(key))
            if kind == "edge":
                orient, row, col = payload  # type: ignore[misc]
                # Single-index lineE is often an X (forbidden edge), skip as wall.
                board.edge(orient, row, col).extra["mark"] = int(value)


def _decode_line(board: LayerBoard, grid: PenpaGrid, data: dict) -> None:
    for key, value in data.items():
        if "," not in str(key):
            continue
        left, right = str(key).split(",", 1)
        k1, p1 = grid.decode_index(int(left))
        k2, p2 = grid.decode_index(int(right))
        if k1 != "cell" or k2 != "cell":
            continue
        r1, c1 = p1  # type: ignore[misc]
        r2, c2 = p2  # type: ignore[misc]
        if r1 == r2 and abs(c1 - c2) == 1:
            board.edge("V", r1, max(c1, c2)).link = 1
        elif c1 == c2 and abs(r1 - r2) == 1:
            board.edge("H", max(r1, r2), c1).link = 1


def encode_penpa(board: LayerBoard, *, title: str = "", tags: list[str] | None = None) -> str:
    """Build a minimal square Penpa+ edit URL from a :class:`LayerBoard`.

    Only surface / number / circle-symbol / lineE are written — enough to
    round-trip the layers this decoder understands.
    """

    grid = PenpaGrid(board.rows, board.cols, 0, 0, 0, 0)
    size = 38
    theta = 0
    title_s = f"Title: {(title or board.title or '').replace(',', '%2C')}"
    author_s = f"Author: {(board.author or '').replace(',', '%2C')}"
    center_n = (2 + grid.top + board.rows // 2) * grid.real_cols + (2 + grid.left + board.cols // 2)
    header = ",".join(
        str(x)
        for x in [
            "square",
            board.cols,
            board.rows,
            size,
            theta,
            1,
            1,
            (board.cols + 1) * size,
            (board.rows + 1) * size,
            center_n,
            center_n,
            0,
            0,
            0,
            0,
            title_s,
            author_s,
            board.source.replace(",", "%2C"),
            "",
            2,
            "false",
            "",
        ]
    )
    pu_q: dict[str, Any] = {
        "surface": {},
        "number": {},
        "symbol": {},
        "line": {},
        "lineE": {},
        "wall": {},
        "cage": {},
        "numberS": {},
        "freeline": {},
        "freelineE": {},
        "thermo": [],
        "arrows": [],
        "direction": [],
        "squareframe": [],
        "polygon": [],
        "deletelineE": {},
        "killercages": [],
        "nobulbthermo": [],
        "command_redo": {"__a": []},
        "command_undo": {"__a": []},
        "command_replay": {"__a": []},
    }

    def centerlist_delta() -> list[int]:
        cells: list[int] = []
        row0 = 2 + grid.top
        col0 = 2 + grid.left
        for row in range(board.rows):
            for col in range(board.cols):
                cells.append((row0 + row) * grid.real_cols + (col0 + col))
        if not cells:
            return []
        out = [cells[0]]
        for prev, cur in zip(cells, cells[1:]):
            out.append(cur - prev)
        return out

    for key, mark in board.cells.items():
        row, col = (int(p) for p in key.split(","))
        index = str(grid.cell_index(row, col))
        if mark.shade:
            pu_q["surface"][index] = 4 if mark.shade == 1 else int(mark.shade)
        if mark.arrow is not None:
            suffix = OURS_DIR_TO_PENPA.get(mark.arrow, "0")
            prefix = "" if mark.number is None else str(mark.number)
            pu_q["number"][index] = [f"{prefix}_{suffix}", 1, "2"]
        elif mark.number is not None:
            pu_q["number"][index] = [str(mark.number), 1, "1"]
        if mark.circle:
            pu_q["symbol"][index] = [int(mark.circle), "circle_M", 1]
        elif mark.star:
            pu_q["symbol"][index] = [1, "star", 1]
        elif mark.cross:
            pu_q["symbol"][index] = [2, "cross", 1]
    for key, mark in board.edges.items():
        if not mark.line:
            continue
        orient, row_s, col_s = key.split(",")
        row, col = int(row_s), int(col_s)
        if orient == "H":
            a = (row, col)
            b = (row, col + 1)
        else:
            a = (row, col)
            b = (row + 1, col)

        def corner_index(rc: tuple[int, int]) -> int:
            pr = rc[0] + 1
            pc = rc[1] + 1
            return pr * grid.real_cols + pc + grid.real_rows * grid.real_cols

        pu_q["lineE"][f"{corner_index(a)},{corner_index(b)}"] = 2

    for side, values in board.outside.items():
        for idx, value in enumerate(values or []):
            if value is None or int(value) < 0:
                continue
            if side == "top":
                pr, pc = 1, idx + 2
            elif side == "bottom":
                pr, pc = 2 + board.rows, idx + 2
            elif side == "left":
                pr, pc = idx + 2, 1
            else:
                pr, pc = idx + 2, 2 + board.cols
            index = str(pr * grid.real_cols + pc)
            pu_q["number"][index] = [str(int(value)), 1, "1"]

    def dump(obj: Any, compress: bool = True) -> str:
        text = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
        return _compress(text) if compress else text

    lines = [
        header,
        dump([0, 0, 0, 0], compress=False),
        dump({}),
        dump(pu_q),
        dump(
            {
                "surface": {},
                "number": {},
                "symbol": {},
                "line": {},
                "lineE": {},
                "polygon": [],
                "command_redo": {"__a": []},
                "command_undo": {"__a": []},
                "command_replay": {"__a": []},
            }
        ),
        dump(centerlist_delta(), compress=False),
        dump([]),
        dump({}),
        "0",
        "0",
        dump([3, 2, 4]),
        "",
        "",
        "0",
        dump({}),
        dump({}),
        dump({}),
        dump(list(tags or board.tags or [])),
        "",
    ]
    payload = _deflate("\n".join(lines))
    return f"https://swaroopg92.github.io/penpa-edit/#m=edit&p={payload}"
