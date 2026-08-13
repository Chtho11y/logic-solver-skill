"""Hover / completion documentation: builtins + ``#`` comments on ``def`` bodies."""

from __future__ import annotations

from pathlib import Path

from puzzle.dsl.builtins import DEBUG_BUILTINS, function_table
from puzzle.dsl.ast_nodes import DefStmt
from puzzle.spec import VarSpec


DEBUG_WARNING = "⚠ 调试用，勿用于正式规则"


def builtin_docs() -> dict[str, tuple[str, str, str]]:
    """``name → (signature, doc, category)`` for every ``function_table`` entry.

    Operators are registered under each token they cover (``==``, ``and``, …)
    so a hover on a single operator can find the row.
    """

    table: dict[str, tuple[str, str, str]] = {}
    for entry in function_table():
        table[entry.name] = (entry.signature, entry.doc, entry.category)
        for alias in _aliases(entry.name):
            table[alias] = (entry.signature, entry.doc, entry.category)
    return table


def _aliases(name: str) -> list[str]:
    mapping = {
        "and / &&": ["and", "&&"],
        "or / ||": ["or", "||"],
        "xor / ^": ["xor", "^"],
        "not / !": ["not", "!"],
        "=>": ["=>"],
        "== != < <= > >=": ["==", "!=", "<", "<=", ">", ">="],
        "+ - * / %": ["+", "-", "*", "/", "%"],
        "c.id": ["id"],
        "c.size": ["size"],
        "c.border": ["border"],
    }
    return mapping.get(name, [])


_BUILTIN_CACHE: dict[str, tuple[str, str, str]] | None = None


def lookup_builtin(name: str) -> tuple[str, str, str] | None:
    global _BUILTIN_CACHE
    if _BUILTIN_CACHE is None:
        _BUILTIN_CACHE = builtin_docs()
    return _BUILTIN_CACHE.get(name)


def is_debug_builtin(name: str) -> bool:
    return name in DEBUG_BUILTINS


def extract_def_doc(source: str, def_line: int) -> str:
    """Scan consecutive ``#`` lines after the ``def`` header (1-based).

    The lexer drops comments, so documentation has to be recovered from the
    original text. Leading blank lines after the header are skipped.
    """

    lines = source.split("\n")
    index = def_line  # 0-based index of the first line *after* the header
    comments: list[str] = []
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped == "":
            if comments:
                break
            index += 1
            continue
        if stripped.startswith("#"):
            comments.append(stripped[1:].lstrip())
            index += 1
            continue
        break
    return "\n".join(comments)


def signature_of(stmt: DefStmt) -> str:
    params = ", ".join(stmt.params)
    return f"{stmt.name}({params})"


def format_builtin_hover(name: str, signature: str, doc: str, category: str) -> str:
    lines = [f"(builtin) {signature}", "─" * 36]
    if doc:
        lines.append(doc)
    if is_debug_builtin(name):
        lines.append(DEBUG_WARNING)
    if category:
        lines.append(f"Category: {category}")
    return "\n".join(lines)


def format_user_hover(signature: str, doc: str, origin: str) -> str:
    lines = [f"(fn) {signature}", "─" * 36]
    if doc:
        lines.append(doc)
    if origin:
        lines.append(origin)
    return "\n".join(lines)


def format_variable_hover(spec: VarSpec) -> str:
    domain = f"[{spec.domain[0]}, {spec.domain[1]}]" if spec.domain else "—"
    lines = [
        f"(variable) {spec.name}",
        "─" * 36,
        f"kind: {spec.kind.value}",
        f"type: {spec.var_type.value}",
        f"domain: {domain}",
    ]
    if spec.doc:
        lines.append(spec.doc)
    return "\n".join(lines)


def format_import_hover(path: Path, names: list[str]) -> str:
    exported = ", ".join(names) if names else "(no defs)"
    return "\n".join(
        [
            f'(import) "{path.stem}"',
            "─" * 36,
            str(path.resolve()),
            f"exports: {exported}",
        ]
    )


def hover_markup(value: str) -> dict:
    return {"kind": "plaintext", "value": value}
