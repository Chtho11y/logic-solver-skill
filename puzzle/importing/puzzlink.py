"""Decode a puzz.link / pzpr URL into a :class:`LayerBoard`.

The URL itself is ``pid/w/h/body``. Typed board contents come from a small
Node helper that opens the puzzle with pzprjs and dumps cells, borders and
outside clues. Python then maps those fields onto our lattices.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

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
    "puzz.link",
}


def looks_like_puzzlink(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    lowered = raw.lower()
    if any(host in lowered for host in ("puzz.link", "pzv.jp", "pzplus", "pzprxs")):
        return True
    if raw.startswith("http") and "/p?" in raw:
        return True
    # Bare ``pid/w/h/body``
    parts = raw.split("/")
    return len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit()


def parse_puzzlink(url: str) -> dict[str, str]:
    """Return ``pid``, ``rows``, ``cols``, ``body``, ``open`` (argument for pzprjs)."""

    raw = (url or "").strip()
    if not raw:
        raise PuzzleImportError("empty puzz.link URL")
    parsed = urlsplit(raw)
    path = unquote(parsed.query or "")
    if not path:
        # ``https://puzz.link/p?slither/5/5/abc`` puts the payload in query
        # without ``=``; urlsplit then keeps it in query. Some mirrors use
        # ``/p.html?slither/...``. Fragment is unused.
        if parsed.query:
            path = unquote(parsed.query)
        elif "?" in raw:
            path = unquote(raw.split("?", 1)[1])
        else:
            path = raw
    if path.startswith("p?"):
        path = path[2:]
    path = path.split("&", 1)[0].strip()
    parts = path.split("/")
    if len(parts) < 3:
        raise PuzzleImportError(f"not a puzz.link puzzle path: {path!r}")
    pid = parts[0]
    try:
        cols = int(parts[1])
        rows = int(parts[2])
    except ValueError as exc:
        raise PuzzleImportError(f"puzz.link size is not numeric: {path!r}") from exc
    body = "/".join(parts[3:])
    return {
        "pid": pid,
        "rows": str(rows),
        "cols": str(cols),
        "body": body,
        "open": path,
        "url": f"https://puzz.link/p?{path}",
        "key": resolve_puzzle_key(pid) or canonical_pid(pid),
    }


def decode_puzzlink(url: str) -> LayerBoard:
    meta = parse_puzzlink(url)
    dumped = _run_pzpr_dump(meta["open"])
    board = layerboard_from_pzpr(dumped)
    board.source = meta["url"]
    board.pid = resolve_puzzle_key(dumped.get("pid") or meta["pid"]) or board.pid
    return board


def _node_path() -> str:
    here = Path(__file__).resolve().parent / "node_modules"
    tmp = Path("/tmp/pzpr-probe/node_modules")
    for candidate in (here, tmp):
        if (candidate / "pzpr").is_dir():
            return str(candidate)
    return ""


def ensure_pzpr() -> None:
    """Install the ``pzpr`` npm package next to ``pzpr_dump.js`` if missing."""

    dest = Path(__file__).resolve().parent
    if (dest / "node_modules" / "pzpr").is_dir():
        return
    npm = shutil.which("npm")
    if not npm:
        return
    subprocess.run(
        [npm, "install", "pzpr@latest", "--no-fund", "--no-audit"],
        cwd=str(dest),
        check=False,
        capture_output=True,
        timeout=120,
    )


def _run_pzpr_dump(open_arg: str) -> dict:
    node = shutil.which("node")
    if not node:
        raise PuzzleImportError("decoding puzz.link URLs needs Node.js (pzprjs)")
    if not DUMP_JS.is_file():
        raise PuzzleImportError(f"missing pzpr dump helper {DUMP_JS}")
    if not _node_path():
        ensure_pzpr()
    env = os.environ.copy()
    node_path = _node_path()
    if node_path:
        env["NODE_PATH"] = node_path + (
            os.pathsep + env["NODE_PATH"] if env.get("NODE_PATH") else ""
        )
    try:
        proc = subprocess.run(
            [node, str(DUMP_JS), open_arg],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise PuzzleImportError("pzprjs timed out opening the puzzle") from exc
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "pzprjs failed").strip().splitlines()[-1:]
        raise PuzzleImportError(err[0] if err else "pzprjs failed")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise PuzzleImportError("pzprjs dump was not JSON") from exc


def layerboard_from_pzpr(dumped: dict) -> LayerBoard:
    rows = int(dumped["rows"])
    cols = int(dumped["cols"])
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
        elif qnum_i == -2:
            mark.shade = 1
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

    if walls:
        board.regions = regions_from_walls(rows, cols, walls)
    return board
