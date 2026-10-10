"""Decode a puzz.link / pzpr URL into a :class:`LayerBoard`.

The URL itself is ``pid/[flags/]w/h/body``. Typed board contents come from a small
Node helper that opens the puzzle with pzprjs and dumps cells, borders and
outside clues. Python then maps those fields onto our lattices.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from .board import LayerBoard, edge_key, regions_from_walls
from .errors import PuzzleImportError
from .pids import canonical_pid, resolve_puzzle_key

DUMP_JS = Path(__file__).resolve().parent / "pzpr_dump.js"

# Hosts that serve the same ``pid/w/h/body`` path as puzz.link.
PUZZLINK_HOSTS = {
    "puzz.link",
    "www.puzz.link",
    "pzv.jp",
    "www.pzv.jp",
    "pzplus.tck.mn",
    "pzprxs.vercel.app",
}

_PID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]*\Z")
_SIZE = re.compile(r"[0-9]+\Z")


def looks_like_puzzlink(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    try:
        parse_puzzlink(raw)
        return True
    except PuzzleImportError:
        # Recognize malformed links on known hosts so the parser can report
        # the actual problem rather than a misleading "neither URL" error.
        try:
            parsed = urlsplit(raw if "://" in raw or raw.startswith("//") else "//" + raw)
            return (parsed.hostname or "").lower() in PUZZLINK_HOSTS
        except ValueError:
            return False


def parse_puzzlink(url: str) -> dict[str, str]:
    """Parse a full/mirror URL or bare ``pid/[flags/]w/h/body`` payload.

    Preserve flags and body verbatim after URL decoding: flags can change the
    puzzle variant or clue encoding, and ``+`` is not a form-encoded space.
    """

    raw = (url or "").strip()
    if not raw:
        raise PuzzleImportError("empty puzz.link URL")
    # urlsplit itself removes literal tabs/newlines. Reject these first so a
    # damaged copied payload cannot silently become a different puzzle.
    if any(char.isspace() or ord(char) < 32 for char in raw):
        raise PuzzleImportError("puzz.link URL must not contain internal whitespace")
    # Browsers often copy a host without the scheme. Normalize only known
    # hosts; an ordinary bare payload must not become a URL hostname.
    if raw.split("/", 1)[0].lower() in PUZZLINK_HOSTS:
        raw = "https://" + raw
    try:
        parsed = urlsplit(raw)
    except ValueError as exc:
        raise PuzzleImportError("invalid puzz.link URL") from exc
    if parsed.scheme and parsed.scheme.lower() not in {"http", "https"}:
        raise PuzzleImportError("puzz.link URLs must use http or https")
    if parsed.netloc and not parsed.query:
        raise PuzzleImportError("puzz.link URL is missing its puzzle payload after '?'")
    encoded = (parsed.query or parsed.path).split("&", 1)[0]
    if re.search(r"%(?![0-9a-fA-F]{2})", encoded):
        raise PuzzleImportError("puzz.link URL contains invalid percent encoding")
    try:
        path = unquote(encoded, errors="strict")
    except UnicodeError as exc:
        raise PuzzleImportError("puzz.link URL contains invalid text encoding") from exc
    if any(char.isspace() or ord(char) < 32 for char in path):
        raise PuzzleImportError("puzz.link puzzle payload must not contain whitespace")
    parts = path.split("/")
    if len(parts) < 3 or not _PID.fullmatch(parts[0]):
        raise PuzzleImportError(f"not a puzz.link puzzle path: {path!r}")
    pid = parts[0]
    # pzpr URLs may have a flags segment, including an explicit empty one.
    size_index = 1 if _SIZE.fullmatch(parts[1]) else 2
    flags = "" if size_index == 1 else parts[1]
    if flags and not re.fullmatch(r"[a-zA-Z]+", flags):
        raise PuzzleImportError(f"invalid puzz.link flags or size: {path!r}")
    if len(parts) <= size_index + 1 or not all(
        _SIZE.fullmatch(value) for value in parts[size_index:size_index + 2]
    ):
        raise PuzzleImportError(f"puzz.link size is not numeric: {path!r}")
    try:
        cols, rows = (int(value) for value in parts[size_index:size_index + 2])
    except ValueError as exc:
        raise PuzzleImportError("puzz.link dimensions are too large") from exc
    if rows <= 0 or cols <= 0:
        raise PuzzleImportError("puzz.link rows and columns must be positive")
    body = "/".join(parts[size_index + 2:])
    return {
        "pid": pid,
        "flags": flags,
        "rows": str(rows),
        "cols": str(cols),
        "body": body,
        "open": path,
        "url": "https://puzz.link/p?" + quote(path, safe="/+.-_~"),
        "key": resolve_puzzle_key(pid) or canonical_pid(pid),
    }


def decode_puzzlink(url: str) -> LayerBoard:
    meta = parse_puzzlink(url)
    dumped = _run_pzpr_dump(meta["open"])
    board = layerboard_from_pzpr(dumped)
    if (board.rows, board.cols) != (int(meta["rows"]), int(meta["cols"])):
        raise PuzzleImportError("pzprjs changed the puzzle dimensions while decoding the URL")
    board.source = meta["url"]
    board.pid = resolve_puzzle_key(dumped.get("pid") or meta["pid"]) or board.pid
    return board


def _run_pzpr_dump(open_arg: str) -> dict:
    node = shutil.which("node")
    if not node:
        raise PuzzleImportError(
            "decoding puzz.link URLs needs Node.js; install Node.js and run "
            "'npm --prefix puzzle/importing install' from the project root"
        )
    if not DUMP_JS.is_file():
        raise PuzzleImportError(f"missing pzpr dump helper {DUMP_JS}")
    try:
        proc = subprocess.run(
            [node, str(DUMP_JS), open_arg],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired as exc:
        raise PuzzleImportError("pzprjs timed out opening the puzzle") from exc
    except OSError as exc:
        raise PuzzleImportError(f"could not start the pzprjs decoder: {exc}") from exc
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "pzprjs failed").strip().splitlines()[:1]
        raise PuzzleImportError(err[0] if err else "pzprjs failed")
    try:
        dumped = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise PuzzleImportError("pzprjs dump was not JSON") from exc
    if not isinstance(dumped, dict):
        raise PuzzleImportError("pzprjs dump was not a board object")
    return dumped


def layerboard_from_pzpr(dumped: dict) -> LayerBoard:
    try:
        rows = int(dumped["rows"])
        cols = int(dumped["cols"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PuzzleImportError("pzprjs dump is missing valid board dimensions") from exc
    if rows <= 0 or cols <= 0:
        raise PuzzleImportError("pzprjs dump has non-positive board dimensions")
    pid = canonical_pid(str(dumped.get("pid") or ""))
    key = resolve_puzzle_key(pid) or pid
    board = LayerBoard(rows=rows, cols=cols, pid=key, tags=[pid] if pid else [])
    walls: set[str] = set()

    for cell in dumped.get("cells") or []:
        row, col = int(cell["r"]), int(cell["c"])
        if not board.in_bounds(row, col):
            continue
        mark = board.cell(row, col)
        qnum = cell.get("qnum")
        if key == "tapa" and cell.get("qnums"):
            mark.number_text = " ".join("?" if int(v) == -2 else str(int(v)) for v in cell["qnums"])
            continue
        qdir = int(cell.get("qdir") or 0)
        ques = int(cell.get("ques") or 0)
        if qdir in {1, 2, 3, 4}:
            mark.arrow = qdir - 1
        if key in {"masyu"}:
            if qnum in {1, 2, 3}:
                # pzpr mashu: 1 = white, 2 = black (same as this repo).
                mark.circle = int(qnum)
            continue
        if key in {"akari"}:
            if qnum is None:
                continue
            qnum = int(qnum)
            if qnum >= 0:
                mark.shade = 1
                mark.number = qnum
            elif qnum == -2:
                mark.shade = 1
            continue
        if qnum is None:
            continue
        try:
            qnum_i = int(qnum)
        except (TypeError, ValueError):
            continue
        if qnum_i >= 0:
            mark.number = qnum_i
        elif qnum_i == -2 and key == "shakashaka":
            # Like Akari, Shakashaka uses -2 for an unnumbered black clue.
            mark.shade = 1
        elif qnum_i == -2:
            # Do not assume that an unspecified number denotes a black cell.
            mark.number_text = "?"
            board.warnings.append(
                f"unknown number clue at {row},{col} is preserved as '?'; "
                "this rule may require a numeric clue before solving"
            )
        if ques:
            mark.extra["ques"] = ques

    for border in dumped.get("borders") or []:
        orient = border.get("orient")
        if orient not in {"H", "V"}:
            continue
        row, col = int(border["r"]), int(border["c"])
        if int(border.get("ques") or 0) == 1:
            walls.add(edge_key(orient, row, col))
            board.edge(orient, row, col).line = 1
        if int(border.get("qans") or 0) == 1:
            board.edge(orient, row, col).line = board.edge(orient, row, col).line or 1

    for item in dumped.get("excells") or []:
        side = item.get("side")
        index = int(item.get("index") or 0)
        qnum = item.get("qnum")
        if side not in {"top", "bottom", "left", "right"}:
            continue
        if qnum is None:
            continue
        try:
            value = int(qnum)
        except (TypeError, ValueError):
            continue
        if value < 0:
            continue
        length = cols if side in {"top", "bottom"} else rows
        arr = board.outside.setdefault(side, [-1] * length)
        while len(arr) < length:
            arr.append(-1)
        if 0 <= index < length:
            arr[index] = value

    if walls or dumped.get("hasGivenRooms") is True:
        board.regions = regions_from_walls(rows, cols, walls)
    return board
