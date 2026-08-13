from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from puzzle.lsp.convert import path_to_uri
from puzzle.lsp.server import LanguageServer


def make_server(debounce: int = 0) -> LanguageServer:
    server = LanguageServer(ROOT)
    server.debounce_ms = debounce
    server.initialize(
        {
            "rootUri": path_to_uri(ROOT),
            "capabilities": {"general": {"positionEncodings": ["utf-32"]}},
            "initializationOptions": {"diagnosticsLevel": "semantic"},
        }
    )
    return server


def open_file(server: LanguageServer, path: Path, text: str | None = None) -> str:
    source = text if text is not None else path.read_text(encoding="utf-8")
    uri = path_to_uri(path)
    server.did_open(
        {
            "textDocument": {
                "uri": uri,
                "languageId": "puzzle-dsl",
                "version": 1,
                "text": source,
            }
        }
    )
    return uri


def token_pos(source: str, value: str, *, after_def: bool = False, occurrence: int = 0):
    from puzzle.dsl.lexer import tokenize
    from puzzle.dsl.tokens import T_KEYWORD, T_NAME, T_STR

    tokens = tokenize(source)
    seen = 0
    for index, token in enumerate(tokens):
        if token.value != value:
            continue
        if after_def:
            prev = tokens[index - 1] if index else None
            if prev is None or not (prev.type == T_KEYWORD and prev.value == "def"):
                continue
        if token.type not in {T_NAME, T_STR, T_KEYWORD} and value != token.value:
            continue
        if seen == occurrence:
            return token.line - 1, token.col - 1
        seen += 1
    raise AssertionError(f"token {value!r} occurrence {occurrence} not found")
