"""Position / range / URI conversion between the DSL compiler and LSP.

The lexer and AST use **1-based** line/column in Unicode code points.
LSP ``Position`` is **0-based**. ``initialize`` prefers ``utf-32`` (code
points, zero conversion); otherwise columns are expressed in UTF-16 code
units.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse, urlunparse


UTF32 = "utf-32"
UTF16 = "utf-16"

# Default until ``initialize`` negotiates otherwise.
DEFAULT_ENCODING = UTF16


def negotiate_encoding(client_encodings: list[str] | None) -> str:
    """Pick ``utf-32`` when the client offers it, else ``utf-16``."""

    if client_encodings:
        lowered = [item.lower() for item in client_encodings]
        if UTF32 in lowered:
            return UTF32
    return UTF16


def _utf16_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def codepoint_to_lsp(line_text: str, offset: int, encoding: str) -> int:
    """Convert a 0-based code-point offset on ``line_text`` to an LSP character."""

    offset = max(0, min(offset, len(line_text)))
    if encoding == UTF32:
        return offset
    return _utf16_len(line_text[:offset])


def lsp_to_codepoint(line_text: str, character: int, encoding: str) -> int:
    """Convert an LSP character offset to a 0-based code-point index."""

    if encoding == UTF32:
        return max(0, min(character, len(line_text)))
    units = 0
    for index, char in enumerate(line_text):
        if units >= character:
            return index
        units += 1 if ord(char) <= 0xFFFF else 2
    return len(line_text)


def line_text(source: str, line_1: int) -> str:
    """Return the (1-based) source line without its newline, or ``\"\"``."""

    lines = source.split("\n")
    index = line_1 - 1
    if 0 <= index < len(lines):
        return lines[index]
    return ""


def position(line_1: int, col_1: int, source: str, encoding: str) -> dict:
    """Build an LSP ``Position`` from 1-based code-point ``line``/``col``."""

    line_0 = max(0, (line_1 or 1) - 1)
    col_0 = max(0, (col_1 or 1) - 1)
    character = codepoint_to_lsp(line_text(source, line_1), col_0, encoding)
    return {"line": line_0, "character": character}


def position_from_lsp(pos: dict, source: str, encoding: str) -> tuple[int, int]:
    """Convert an LSP ``Position`` to 1-based ``(line, col)`` code points."""

    line_0 = int(pos.get("line", 0))
    character = int(pos.get("character", 0))
    col_0 = lsp_to_codepoint(line_text(source, line_0 + 1), character, encoding)
    return line_0 + 1, col_0 + 1


def line_end_character(source: str, line_1: int, encoding: str) -> int:
    return codepoint_to_lsp(line_text(source, line_1), len(line_text(source, line_1)), encoding)


def range_at(line_1: int, col_1: int, length: int, source: str, encoding: str) -> dict:
    """A range covering ``length`` code points starting at ``line``/``col``."""

    start = position(line_1, col_1, source, encoding)
    end_col_0 = max(0, (col_1 or 1) - 1) + max(0, length)
    end = {
        "line": start["line"],
        "character": codepoint_to_lsp(line_text(source, line_1), end_col_0, encoding),
    }
    return {"start": start, "end": end}


def range_to_eol(line_1: int, col_1: int, source: str, encoding: str) -> dict:
    """A range from ``line``/``col`` to the end of that line."""

    start = position(line_1, col_1, source, encoding)
    end = {"line": start["line"], "character": line_end_character(source, line_1, encoding)}
    return {"start": start, "end": end}


def range_whole_line(line_1: int, source: str, encoding: str) -> dict:
    return range_to_eol(line_1, 1, source, encoding)


def token_length(value: str, token_type: str) -> int:
    """Code-point length of a token's source span.

    String tokens store the unquoted value; the source span includes quotes.
    """

    if token_type == "STR":
        return len(value) + 2
    return len(value) if value else 0


def path_to_uri(path: Path) -> str:
    return path.resolve().as_uri()


def uri_to_path(uri: str) -> Path:
    parsed = urlparse(uri)
    path = unquote(parsed.path)
    if os.name == "nt":
        if parsed.netloc:
            path = f"//{parsed.netloc}{path}"
        elif len(path) >= 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        elif len(path) >= 3 and path[0] == "/" and path[2] == "|":
            path = path[1] + ":" + path[3:]
    return Path(path)


def file_location(path: Path, line_1: int, col_1: int, source: str, encoding: str, length: int = 1) -> dict:
    return {
        "uri": path_to_uri(path),
        "range": range_at(line_1, col_1, length, source, encoding),
    }


def relative_display(path: Path, root: Path | None) -> str:
    """Pretty path for hover footers (``puzzle/lib/shading.dsl:42``)."""

    resolved = path.resolve()
    if root is not None:
        try:
            return resolved.relative_to(root.resolve()).as_posix()
        except ValueError:
            pass
    return resolved.as_posix()


def normalize_uri(uri: str) -> str:
    """Canonicalise a file URI so the same path always hashes the same."""

    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return uri
    path = uri_to_path(uri)
    try:
        return path.resolve().as_uri()
    except OSError:
        return urlunparse(parsed)
