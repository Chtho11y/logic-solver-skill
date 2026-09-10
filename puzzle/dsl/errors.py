"""Error types for the puzzle DSL pipeline (lexer / parser / compiler).

All errors carry an optional ``line``/``col`` so the UI can point the user at
the offending source location. UI-independent (no PyQt import).
"""

from __future__ import annotations


class DSLError(Exception):
    """Base class for every DSL failure (lexing, parsing, compiling)."""

    def __init__(self, message: str, line: int | None = None, col: int | None = None) -> None:
        self.message = message
        self.line = line
        self.col = col
        super().__init__(self._format())

    def _format(self) -> str:
        if self.line is not None:
            return f"line {self.line}: {self.message}"
        return self.message


class LexError(DSLError):
    """Raised when the source cannot be tokenised."""


class ParseError(DSLError):
    """Raised when the token stream is not a valid program."""


class CompileError(DSLError):
    """Raised when a well-formed program cannot be lowered to constraints."""
