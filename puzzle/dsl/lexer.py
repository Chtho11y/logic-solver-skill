"""Lexer for the puzzle DSL.

Produces a flat token stream with Python-style significant indentation:
``INDENT`` / ``DEDENT`` tokens delimit blocks and ``NEWLINE`` terminates logical
lines. Blank lines and ``#`` comments are ignored. Newlines inside ``(`` / ``[``
are treated as line continuations.

UI-independent (no PyQt import).
"""

from __future__ import annotations

from .errors import LexError
from .tokens import (
    KEYWORDS,
    ONE_CHAR_OPS,
    T_DEDENT,
    T_EOF,
    T_INDENT,
    T_INT,
    T_KEYWORD,
    T_NAME,
    T_NEWLINE,
    T_OP,
    T_STR,
    TWO_CHAR_OPS,
    Token,
)


def tokenize(source: str) -> list[Token]:
    """Tokenise ``source`` into a list ending with an ``EOF`` token."""

    return _Lexer(source).run()


class _Lexer:
    def __init__(self, source: str) -> None:
        # Normalise newlines; keep a trailing newline so the last line closes.
        self._src = source.replace("\r\n", "\n").replace("\r", "\n")
        self._tokens: list[Token] = []
        self._indents: list[int] = [0]
        self._depth = 0  # bracket nesting depth

    def run(self) -> list[Token]:
        lines = self._src.split("\n")
        for lineno, raw in enumerate(lines, start=1):
            self._consume_line(lineno, raw)
        # Close any open blocks and finish the stream.
        last_line = len(lines)
        while len(self._indents) > 1:
            self._indents.pop()
            self._tokens.append(Token(T_DEDENT, "", last_line, 0))
        self._tokens.append(Token(T_EOF, "", last_line, 0))
        return self._tokens

    # -- per-line handling ----------------------------------------------

    def _consume_line(self, lineno: int, raw: str) -> None:
        if self._depth > 0:
            # Continuation line inside brackets: no indentation handling.
            self._scan_tokens(lineno, raw, 0)
            return

        indent, rest, col0 = self._measure_indent(raw)
        stripped = rest.lstrip()
        if stripped == "" or stripped.startswith("#"):
            return  # blank or comment-only line: emit nothing

        self._handle_indentation(lineno, indent)
        self._scan_tokens(lineno, rest, col0)
        # A logical line ends here unless a bracket is still open.
        if self._depth == 0 and self._tokens and self._tokens[-1].type != T_NEWLINE:
            self._tokens.append(Token(T_NEWLINE, "", lineno, len(raw)))

    def _measure_indent(self, raw: str) -> tuple[int, str, int]:
        col = 0
        for ch in raw:
            if ch == " ":
                col += 1
            elif ch == "\t":
                col += 8 - (col % 8)
            else:
                break
        return col, raw[self._leading_ws_len(raw):], self._leading_ws_len(raw)

    @staticmethod
    def _leading_ws_len(raw: str) -> int:
        i = 0
        for ch in raw:
            if ch in " \t":
                i += 1
            else:
                break
        return i

    def _handle_indentation(self, lineno: int, indent: int) -> None:
        if indent > self._indents[-1]:
            self._indents.append(indent)
            self._tokens.append(Token(T_INDENT, "", lineno, 0))
            return
        while indent < self._indents[-1]:
            self._indents.pop()
            self._tokens.append(Token(T_DEDENT, "", lineno, 0))
        if indent != self._indents[-1]:
            raise LexError("inconsistent indentation", lineno, indent)

    # -- token scanning -------------------------------------------------

    def _scan_tokens(self, lineno: int, text: str, col_offset: int) -> None:
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            col = col_offset + i + 1  # 1-based column
            if ch in " \t":
                i += 1
                continue
            if ch == "#":
                break  # rest of line is a comment
            if ch.isdigit():
                j = i
                while j < n and text[j].isdigit():
                    j += 1
                self._tokens.append(Token(T_INT, text[i:j], lineno, col))
                i = j
                continue
            if ch in "\"'":
                value, i = self._scan_string(lineno, text, i, col)
                self._tokens.append(Token(T_STR, value, lineno, col))
                continue
            if ch.isalpha() or ch == "_":
                j = i
                while j < n and (text[j].isalnum() or text[j] == "_"):
                    j += 1
                word = text[i:j]
                ttype = T_KEYWORD if word in KEYWORDS else T_NAME
                self._tokens.append(Token(ttype, word, lineno, col))
                i = j
                continue
            two = text[i : i + 2]
            if two in TWO_CHAR_OPS:
                self._tokens.append(Token(T_OP, two, lineno, col))
                i += 2
                continue
            if ch in ONE_CHAR_OPS:
                if ch in "([":
                    self._depth += 1
                elif ch in ")]":
                    self._depth = max(0, self._depth - 1)
                self._tokens.append(Token(T_OP, ch, lineno, col))
                i += 1
                continue
            raise LexError(f"unexpected character {ch!r}", lineno, col)

    @staticmethod
    def _scan_string(lineno: int, text: str, start: int, col: int) -> tuple[str, int]:
        """Scan a single-line ``"..."`` / ``'...'`` literal, returning its value."""

        quote = text[start]
        out: list[str] = []
        i = start + 1
        while i < len(text):
            ch = text[i]
            if ch == "\\" and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                return "".join(out), i + 1
            out.append(ch)
            i += 1
        raise LexError("unterminated string literal", lineno, col)
