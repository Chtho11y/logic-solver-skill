"""Token definitions for the puzzle DSL lexer.

UI-independent (no PyQt import).
"""

from __future__ import annotations

from dataclasses import dataclass

# Token type tags.
T_INT = "INT"
T_STR = "STR"
T_NAME = "NAME"
T_KEYWORD = "KEYWORD"
T_OP = "OP"
T_NEWLINE = "NEWLINE"
T_INDENT = "INDENT"
T_DEDENT = "DEDENT"
T_EOF = "EOF"

KEYWORDS = frozenset(
    {
        "if", "elif", "else", "for", "in", "let", "and", "or", "not",
        "true", "false", "def", "return", "import",
    }
)

# Multi-character operators must be tried before single-character ones.
# ``&&`` / ``||`` are symbolic aliases for ``and`` / ``or``; ``^`` is xor and
# ``!`` is not (``!=`` is matched first because two-char ops have priority).
# ``=>`` is implies (matched before single ``=``/``>``); ``.`` is member access.
_TWO_CHAR_OPS = ("==", "!=", "<=", ">=", "&&", "||", "=>")
_ONE_CHAR_OPS = "+-*/%<>=()[],:^!."
OPERATORS = frozenset(list(_TWO_CHAR_OPS) + list(_ONE_CHAR_OPS))
TWO_CHAR_OPS = _TWO_CHAR_OPS
ONE_CHAR_OPS = _ONE_CHAR_OPS


@dataclass(frozen=True)
class Token:
    type: str
    value: str
    line: int
    col: int

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.col})"
