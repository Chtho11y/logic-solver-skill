"""LSP handlers: capabilities, diagnostics, hover, definition, tokens, symbols."""

from __future__ import annotations

import json
import re
import sys
import threading
from pathlib import Path
from typing import Any

from puzzle.dsl.builtins import BUILTIN_FUNCTIONS, DEBUG_BUILTINS, DIRECTION_CONSTANTS
from puzzle.dsl.errors import CompileError, DSLError, LexError, ParseError
from puzzle.dsl.lexer import tokenize
from puzzle.dsl.parser import parse
from puzzle.dsl.solver import is_available as z3_available
from puzzle.dsl.tokens import (
    T_DEDENT,
    T_EOF,
    T_INDENT,
    T_INT,
    T_KEYWORD,
    T_NAME,
    T_NEWLINE,
    T_OP,
    T_STR,
    Token,
)
from puzzle.spec import (
    PuzzleSpec,
    VarSpec,
    build_grid,
    build_params,
    build_regions,
    build_variables,
    make_loader,
)

from . import convert
from .convert import (
    UTF32,
    file_location,
    line_text,
    normalize_uri,
    path_to_uri,
    position,
    position_from_lsp,
    range_at,
    range_to_eol,
    relative_display,
    token_length,
    uri_to_path,
)
from .docs import (
    format_builtin_hover,
    format_import_hover,
    format_user_hover,
    format_variable_hover,
    hover_markup,
    lookup_builtin,
)
from .index import (
    Index,
    LocalBinding,
    Symbol,
    collect_let_for_lines,
    enclosing_def_params,
    locals_covering,
    node_end_line,
    resolve_module,
    walk_nodes,
)
from .rpc import METHOD_NOT_FOUND, Rpc, RpcError
from .workspace import Document, Workspace


TOKEN_TYPES = ["keyword", "number", "string", "operator", "function", "parameter", "variable"]
TOKEN_MODIFIERS = ["declaration", "defaultLibrary", "deprecated", "definition", "readonly"]

_TYPE_INDEX = {name: index for index, name in enumerate(TOKEN_TYPES)}
_MOD_INDEX = {name: index for index, name in enumerate(TOKEN_MODIFIERS)}

SKIP_TOKEN_TYPES = {T_NEWLINE, T_INDENT, T_DEDENT, T_EOF}

BUILTIN_CONSTANTS = frozenset({"rows", "cols", *DIRECTION_CONSTANTS})

SYMBOL_FUNCTION = 12
SYMBOL_VARIABLE = 13


class LanguageServer:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root
        self.rpc: Rpc | None = None
        self.workspace = Workspace()
        self.index = Index(root)
        self.encoding = convert.DEFAULT_ENCODING
        self.diagnostics_level = "semantic"
        self.debounce_ms = 200
        self.shutdown_requested = False
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
        self.published: list[dict] = []

    # -- dispatch -------------------------------------------------------

    def dispatch(self, method: str, params: Any) -> Any:
        handler = _HANDLERS.get(method)
        if handler is None:
            if method.startswith("$/") or method in _NOTIFICATIONS:
                return None
            raise RpcError(METHOD_NOT_FOUND, f"method not found: {method}")
        return handler(self, params or {})

    # -- lifecycle ------------------------------------------------------

    def initialize(self, params: dict) -> dict:
        root = _root_from_init(params)
        if root is not None:
            self.root = root
            self.index = Index(root)
        encodings = (
            ((params.get("capabilities") or {}).get("general") or {}).get("positionEncodings")
        )
        self.encoding = convert.negotiate_encoding(encodings)
        options = params.get("initializationOptions") or {}
        level = options.get("diagnosticsLevel") or options.get("diagnostics")
        if isinstance(level, str) and level in {"off", "syntax", "semantic"}:
            self.diagnostics_level = level
        self.index.build()
        return {
            "capabilities": {
                "positionEncoding": self.encoding,
                "textDocumentSync": {
                    "openClose": True,
                    "change": 1,
                    "save": {"includeText": False},
                },
                "semanticTokensProvider": {
                    "legend": {
                        "tokenTypes": TOKEN_TYPES,
                        "tokenModifiers": TOKEN_MODIFIERS,
                    },
                    "full": True,
                    "range": False,
                },
                "hoverProvider": True,
                "definitionProvider": True,
                "referencesProvider": True,
                "documentSymbolProvider": True,
                "workspaceSymbolProvider": True,
                "completionProvider": {"triggerCharacters": ["(", ",", "\""]},
                "signatureHelpProvider": {"triggerCharacters": ["(", ","]},
            },
            "serverInfo": {"name": "puzzle-dsl-lsp", "version": "0.1.0"},
        }

    def initialized(self, _params: dict) -> None:
        return None

    def shutdown(self, _params: dict) -> None:
        self.shutdown_requested = True
        self._cancel_timers()
        return None

    def exit(self, _params: dict) -> None:
        self._cancel_timers()
        if self.rpc is not None:
            self.rpc.stop()
        # ``main()`` maps ``shutdown_requested`` to the process exit code.

    def did_change_configuration(self, params: dict) -> None:
        settings = params.get("settings") or {}
        dsl = settings.get("puzzleDsl") or settings
        level = None
        if isinstance(dsl, dict):
            diag = dsl.get("diagnostics")
            if isinstance(diag, dict):
                level = diag.get("level")
            elif isinstance(diag, str):
                level = diag
            level = level or dsl.get("diagnostics.level")
        if isinstance(level, str) and level in {"off", "syntax", "semantic"}:
            self.diagnostics_level = level
            for uri in list(self.workspace.documents):
                self._diagnose(uri)

    # -- documents ------------------------------------------------------

    def did_open(self, params: dict) -> None:
        item = params.get("textDocument") or {}
        uri = normalize_uri(item.get("uri", ""))
        text = item.get("text", "")
        self.workspace.open(uri, item.get("languageId", "puzzle-dsl"), item.get("version", 0), text)
        self.index.index_uri(uri, text, uri_to_path(uri))
        self._diagnose(uri, include_semantic=True)

    def did_change(self, params: dict) -> None:
        item = params.get("textDocument") or {}
        uri = normalize_uri(item.get("uri", ""))
        changes = params.get("contentChanges") or []
        if not changes:
            return
        text = changes[-1].get("text", "")
        self.workspace.change(uri, item.get("version", 0), text)
        self.index.index_uri(uri, text, uri_to_path(uri))
        self._schedule_diagnose(uri)

    def did_save(self, params: dict) -> None:
        item = params.get("textDocument") or {}
        uri = normalize_uri(item.get("uri", ""))
        doc = self.workspace.get(uri)
        if doc is not None:
            self.index.index_uri(uri, doc.text, uri_to_path(uri))
            for dep in self.index.dependents(uri):
                dep_doc = self.workspace.get(dep)
                if dep_doc is not None:
                    self.index.index_uri(dep, dep_doc.text, uri_to_path(dep))
                else:
                    self.index.index_path(uri_to_path(dep))
        self._diagnose(uri, include_semantic=True)

    def did_close(self, params: dict) -> None:
        item = params.get("textDocument") or {}
        uri = normalize_uri(item.get("uri", ""))
        self._cancel_timer(uri)
        self.workspace.close(uri)
        self._publish(uri, [])

    def did_change_watched_files(self, params: dict) -> None:
        for change in params.get("changes") or []:
            uri = normalize_uri(change.get("uri", ""))
            if not uri.endswith(".dsl"):
                continue
            path = uri_to_path(uri)
            if change.get("type") == 3 or not path.is_file():
                self.index.drop(uri)
                continue
            doc = self.workspace.get(uri)
            if doc is not None:
                self.index.index_uri(uri, doc.text, path)
            else:
                self.index.index_path(path)

    # -- diagnostics ----------------------------------------------------

    def _schedule_diagnose(self, uri: str) -> None:
        if self.debounce_ms <= 0:
            self._diagnose(uri, include_semantic=False)
            return
        self._cancel_timer(uri)

        def fire() -> None:
            self._diagnose(uri, include_semantic=False)

        timer = threading.Timer(self.debounce_ms / 1000.0, fire)
        timer.daemon = True
        self._timers[uri] = timer
        timer.start()

    def _cancel_timer(self, uri: str) -> None:
        timer = self._timers.pop(uri, None)
        if timer is not None:
            timer.cancel()

    def _cancel_timers(self) -> None:
        for uri in list(self._timers):
            self._cancel_timer(uri)

    def _diagnose(self, uri: str, include_semantic: bool = False) -> None:
        if self.diagnostics_level == "off":
            self._publish(uri, [])
            return
        doc = self.workspace.get(uri)
        text = doc.text if doc is not None else None
        if text is None:
            path = uri_to_path(uri)
            if path.is_file():
                text = path.read_text(encoding="utf-8")
            else:
                self._publish(uri, [])
                return
        diags = self._t1(text)
        if (
            include_semantic
            and not diags
            and self.diagnostics_level == "semantic"
        ):
            diags.extend(self._t2(uri, text))
        self._publish(uri, diags)

    def _t1(self, text: str) -> list[dict]:
        try:
            parse(text)
        except (LexError, ParseError, DSLError) as exc:
            return [self._diagnostic(text, exc.message, exc.line, exc.col)]
        except Exception as exc:  # noqa: BLE001
            return [self._diagnostic(text, f"internal parse error: {exc}", 1, 1)]
        return []

    def _t2(self, uri: str, text: str) -> list[dict]:
        spec = self._spec_for(uri)
        if spec is None:
            return []
        sample = self._sample_for(uri, spec.key)
        if sample is None or not z3_available():
            return []
        try:
            from puzzle.dsl.compiler import compile_source
            import z3
        except Exception:
            return []
        grid = build_grid(sample)
        variables = build_variables(spec, sample, grid)
        regions = build_regions(spec, sample, grid)
        params = build_params(spec, sample)
        try:
            compile_source(text, grid, variables, regions, z3, params, make_loader())
        except CompileError as exc:
            return [self._diagnostic(text, exc.message, exc.line, exc.col)]
        except DSLError as exc:
            return [self._diagnostic(text, exc.message, exc.line, exc.col)]
        except Exception:
            return []
        return []

    def _diagnostic(self, text: str, message: str, line: int | None, col: int | None) -> dict:
        line_1 = line or 1
        col_1 = col or 1
        return {
            "range": range_to_eol(line_1, col_1, text, self.encoding),
            "severity": 1,
            "source": "puzzle-dsl",
            "message": message,
        }

    def _publish(self, uri: str, diagnostics: list[dict]) -> None:
        payload = {"uri": uri, "diagnostics": diagnostics}
        self.published.append(payload)
        if self.rpc is not None:
            self.rpc.notify("textDocument/publishDiagnostics", payload)

    # -- semantic tokens ------------------------------------------------

    def semantic_tokens(self, params: dict) -> dict:
        uri, doc = self._doc(params)
        if doc is None:
            return {"data": []}
        try:
            tokens = tokenize(doc.text)
        except DSLError:
            return {"data": []}
        program = self._program(uri, doc.text)
        user_fns = set(self.index.visible_functions(uri))
        puzzle_vars = {item.name for item in self._variables_for(uri)}
        let_for = collect_let_for_lines(program) if program is not None else {}
        data: list[int] = []
        prev_line = 0
        prev_start = 0
        for index, token in enumerate(tokens):
            if token.type in SKIP_TOKEN_TYPES:
                continue
            nxt = tokens[index + 1] if index + 1 < len(tokens) else None
            prev = tokens[index - 1] if index > 0 else None
            kind, mods = self._classify(token, prev, nxt, program, user_fns, puzzle_vars, let_for)
            if kind is None:
                continue
            line_0 = token.line - 1
            start = convert.codepoint_to_lsp(line_text(doc.text, token.line), token.col - 1, self.encoding)
            length = self._encoded_token_length(doc.text, token)
            if length <= 0:
                continue
            delta_line = line_0 - prev_line
            delta_start = start - prev_start if delta_line == 0 else start
            data.extend([delta_line, delta_start, length, _TYPE_INDEX[kind], mods])
            prev_line = line_0
            prev_start = start
        return {"data": data}

    def _encoded_token_length(self, text: str, token: Token) -> int:
        span = self._token_source(text, token)
        return convert.codepoint_to_lsp(span, len(span), self.encoding) if self.encoding != UTF32 else len(span)

    def _token_source(self, text: str, token: Token) -> str:
        raw = line_text(text, token.line)
        start = max(0, token.col - 1)
        length = token_length(token.value, token.type)
        if token.type == T_STR:
            return raw[start : start + length] or ('"' + token.value + '"')
        if length:
            return raw[start : start + length] or token.value
        return token.value

    def _classify(
        self,
        token: Token,
        prev: Token | None,
        nxt: Token | None,
        program,
        user_fns: set[str],
        puzzle_vars: set[str],
        let_for: dict[int, set[str]],
    ) -> tuple[str | None, int]:
        if token.type == T_KEYWORD:
            return "keyword", 0
        if token.type == T_INT:
            return "number", 0
        if token.type == T_STR:
            return "string", 0
        if token.type == T_OP:
            return "operator", 0
        if token.type != T_NAME:
            return None, 0
        name = token.value
        callish = nxt is not None and nxt.type == T_OP and nxt.value == "("
        if prev is not None and prev.type == T_KEYWORD and prev.value == "def":
            return "function", _mod("declaration")
        if name in BUILTIN_FUNCTIONS and callish:
            mods = _mod("defaultLibrary")
            if name in DEBUG_BUILTINS:
                mods |= _mod("deprecated")
            return "function", mods
        if name in user_fns and callish:
            return "function", 0
        if program is not None and name in enclosing_def_params(program, token.line):
            return "parameter", 0
        if name in let_for.get(token.line, set()) and prev is not None and prev.value in {"let", "for", ","}:
            return "variable", _mod("definition")
        if name in puzzle_vars:
            return "variable", _mod("readonly")
        return "variable", 0

    # -- hover / definition / references --------------------------------

    def hover(self, params: dict) -> dict | None:
        hit = self._hit(params)
        if hit is None:
            return None
        uri, doc, token = hit
        rendered = self._hover_text(uri, doc, token, params)
        if not rendered:
            return None
        length = token_length(token.value, token.type) or len(token.value) or 1
        return {
            "contents": hover_markup(rendered),
            "range": range_at(token.line, token.col, length, doc.text, self.encoding),
        }

    def definition(self, params: dict) -> dict | list | None:
        hit = self._hit(params)
        if hit is None:
            return None
        uri, doc, token = hit
        loc = self._definition_of(uri, doc, token)
        return loc

    def references(self, params: dict) -> list[dict]:
        hit = self._hit(params)
        if hit is None:
            return []
        uri, doc, token = hit
        include_decl = bool((params.get("context") or {}).get("includeDeclaration", True))
        return self._references_of(uri, doc, token, include_decl)

    def _hover_text(self, uri: str, doc: Document, token: Token, params: dict) -> str | None:
        name = token.value
        if token.type == T_STR:
            imp = self._import_at(uri, doc, token)
            if imp is not None:
                path, names = imp
                return format_import_hover(path, names)
            return None
        if token.type == T_OP or (token.type == T_KEYWORD and name in {"and", "or", "not"}):
            builtin = lookup_builtin(name)
            if builtin:
                return format_builtin_hover(name, *builtin)
            return None
        if token.type != T_NAME and token.type != T_KEYWORD:
            return None
        resolved = self._resolve_name(uri, doc, token)
        if resolved is None:
            return None
        kind, payload = resolved
        if kind == "builtin":
            builtin = lookup_builtin(name)
            if builtin is None:
                return None
            return format_builtin_hover(name, *builtin)
        if kind == "function":
            sym: Symbol = payload
            origin = f"{self._display_path(uri_to_path(sym.uri))}:{sym.line}"
            sig = f"{sym.name}({', '.join(sym.params)})"
            return format_user_hover(sig, sym.doc, origin)
        if kind == "variable":
            return format_variable_hover(payload)
        if kind == "local":
            binding: LocalBinding = payload
            return f"({binding.kind}) {binding.name}"
        if kind == "member":
            builtin = lookup_builtin(payload) or lookup_builtin(name)
            if builtin:
                return format_builtin_hover(name, *builtin)
        if kind == "constant":
            builtin = lookup_builtin(name)
            if builtin:
                return format_builtin_hover(name, *builtin)
        return None

    def _definition_of(self, uri: str, doc: Document, token: Token) -> dict | None:
        if token.type == T_STR:
            imp = self._import_at(uri, doc, token)
            if imp is None:
                return None
            path, _names = imp
            text = path.read_text(encoding="utf-8") if path.is_file() else ""
            return file_location(path, 1, 1, text, self.encoding, 1)
        if token.type != T_NAME:
            return None
        resolved = self._resolve_name(uri, doc, token)
        if resolved is None:
            return None
        kind, payload = resolved
        if kind == "builtin" or kind == "constant" or kind == "member":
            return None
        if kind == "function":
            sym: Symbol = payload
            path = uri_to_path(sym.uri)
            text = self._text_of(sym.uri, path)
            return file_location(path, sym.line, sym.col, text, self.encoding, len(sym.name))
        if kind == "variable":
            spec: VarSpec = payload
            json_path = self._json_for(uri)
            if json_path is None or not json_path.is_file():
                return None
            text = json_path.read_text(encoding="utf-8")
            loc = _find_json_var(text, spec.name)
            if loc is None:
                return file_location(json_path, 1, 1, text, self.encoding, 1)
            line, col, length = loc
            return file_location(json_path, line, col, text, self.encoding, length)
        if kind == "local":
            binding: LocalBinding = payload
            return file_location(
                uri_to_path(uri),
                binding.line,
                binding.col,
                doc.text,
                self.encoding,
                len(binding.name),
            )
        return None

    def _references_of(self, uri: str, doc: Document, token: Token, include_decl: bool) -> list[dict]:
        if token.type != T_NAME:
            return []
        name = token.value
        resolved = self._resolve_name(uri, doc, token)
        locations: list[dict] = []
        if resolved is not None and resolved[0] == "function":
            sym: Symbol = resolved[1]
            if include_decl:
                text = self._text_of(sym.uri, uri_to_path(sym.uri))
                locations.append(
                    file_location(uri_to_path(sym.uri), sym.line, sym.col, text, self.encoding, len(sym.name))
                )
            for file_uri, entry in self.index.files.items():
                visible = self.index.visible_functions(file_uri)
                if visible.get(name) is None or visible[name].uri != sym.uri:
                    continue
                locations.extend(self._name_uses(file_uri, entry.text, name, skip_def=True))
            return _unique_locations(locations)
        if resolved is not None and resolved[0] == "variable":
            locations.extend(self._name_uses(uri, doc.text, name, skip_def=False))
            return _unique_locations(locations)
        if resolved is not None and resolved[0] == "local":
            binding: LocalBinding = resolved[1]
            program = self._program(uri, doc.text)
            end = binding.line
            if program is not None:
                for node in walk_nodes(program):
                    if hasattr(node, "line") and node.line >= binding.line:
                        end = max(end, node_end_line(node) if hasattr(node, "body") or hasattr(node, "statements") else getattr(node, "line", end))
            locations.extend(
                self._name_uses(uri, doc.text, name, skip_def=not include_decl, line_min=binding.line, line_max=end)
            )
            return _unique_locations(locations)
        return []

    def _name_uses(
        self,
        uri: str,
        text: str,
        name: str,
        skip_def: bool = False,
        line_min: int = 0,
        line_max: int = 10**9,
    ) -> list[dict]:
        try:
            tokens = tokenize(text)
        except DSLError:
            return []
        out: list[dict] = []
        prev = None
        for token in tokens:
            if token.type == T_NAME and token.value == name and line_min <= token.line <= line_max:
                if skip_def and prev is not None and prev.type == T_KEYWORD and prev.value == "def":
                    prev = token
                    continue
                out.append(
                    file_location(uri_to_path(uri), token.line, token.col, text, self.encoding, len(name))
                )
            prev = token
        return out

    def _resolve_name(self, uri: str, doc: Document, token: Token) -> tuple[str, Any] | None:
        """Lookup chain: local → puzzle var → constant → user fn → builtin."""

        name = token.value
        if token.type == T_NAME and self._is_member_attr(doc.text, token):
            return "member", name
        program = self._program(uri, doc.text)
        if program is not None:
            locals_here = locals_covering(program, token.line)
            if name in locals_here:
                return "local", locals_here[name]
        for spec in self._variables_for(uri):
            if spec.name == name:
                return "variable", spec
        if name in BUILTIN_CONSTANTS:
            return "constant", name
        sym = self.index.find_function(uri, name)
        if sym is not None:
            return "function", sym
        if name in BUILTIN_FUNCTIONS or lookup_builtin(name):
            return "builtin", name
        return None

    def _is_member_attr(self, text: str, token: Token) -> bool:
        try:
            tokens = tokenize(text)
        except DSLError:
            return False
        for index, item in enumerate(tokens):
            if item.line == token.line and item.col == token.col and item.value == token.value:
                prev = tokens[index - 1] if index else None
                return prev is not None and prev.type == T_OP and prev.value == "."
        return False

    def _import_at(self, uri: str, doc: Document, token: Token) -> tuple[Path, list[str]] | None:
        if token.type != T_STR:
            return None
        try:
            tokens = tokenize(doc.text)
        except DSLError:
            return None
        for index, item in enumerate(tokens):
            if item.line == token.line and item.col == token.col:
                prev = tokens[index - 1] if index else None
                if prev is None or not (prev.type == T_KEYWORD and prev.value == "import"):
                    return None
                path = resolve_module(token.value, self.index.search)
                if path is None:
                    return None
                imported = self.index.files.get(path_to_uri(path))
                if imported is None:
                    imported = self.index.index_path(path)
                names = [sym.name for sym in (imported.symbols if imported else []) if not sym.nested]
                return path, names
        return None

    # -- symbols / completion / signature --------------------------------

    def document_symbol(self, params: dict) -> list[dict]:
        uri, doc = self._doc(params)
        if doc is None:
            return []
        entry = self.index.files.get(uri)
        if entry is None:
            return []
        return [self._symbol_info(sym, doc.text) for sym in entry.symbols if not sym.nested]

    def workspace_symbol(self, params: dict) -> list[dict]:
        query = (params.get("query") or "").lower()
        out: list[dict] = []
        for sym in self.index.all_symbols():
            if query and query not in sym.name.lower():
                continue
            text = self._text_of(sym.uri, uri_to_path(sym.uri))
            info = self._symbol_info(sym, text)
            info["location"] = {
                "uri": sym.uri,
                "range": info["range"],
            }
            out.append(info)
        return out

    def _symbol_info(self, sym: Symbol, text: str) -> dict:
        sel = range_at(sym.line, sym.col, len(sym.name), text, self.encoding)
        end_line = sym.end_line or sym.line
        full = {
            "start": position(sym.line, 1, text, self.encoding),
            "end": {
                "line": max(0, end_line - 1),
                "character": convert.line_end_character(text, end_line, self.encoding),
            },
        }
        return {
            "name": f"{sym.name}({', '.join(sym.params)})",
            "kind": SYMBOL_FUNCTION,
            "range": full,
            "selectionRange": sel,
        }

    def completion(self, params: dict) -> dict:
        uri, doc = self._doc(params)
        items: list[dict] = []
        seen: set[str] = set()

        def add(label: str, kind: int, detail: str = "", doc: str = "") -> None:
            if label in seen:
                return
            seen.add(label)
            item: dict[str, Any] = {"label": label, "kind": kind}
            if detail:
                item["detail"] = detail
            if doc:
                item["documentation"] = doc
            items.append(item)

        if doc is not None:
            line_1, _col = position_from_lsp(params.get("position") or {}, doc.text, self.encoding)
            line = line_text(doc.text, line_1)
            if "import" in line and '"' in line:
                for folder in self.index.search:
                    for path in sorted(folder.glob("*.dsl")):
                        add(path.stem, 17, str(path))  # File
                return {"isIncomplete": False, "items": items}
            program = self._program(uri, doc.text)
            if program is not None:
                for name, binding in locals_covering(program, line_1).items():
                    add(name, 6, binding.kind)  # Variable
            for spec in self._variables_for(uri):
                add(spec.name, 6, f"{spec.kind.value} {spec.var_type.value}", spec.doc)
            for sym in self.index.visible_functions(uri).values():
                add(sym.name, 3, f"{sym.name}({', '.join(sym.params)})", sym.doc)
        from puzzle.dsl.builtins import function_table

        for entry in function_table():
            if " " in entry.name or "/" in entry.name:
                continue
            add(entry.name, 3 if entry.category not in {"Constant", "Operator"} else 21, entry.signature, entry.doc)
        return {"isIncomplete": False, "items": items}

    def signature_help(self, params: dict) -> dict | None:
        uri, doc = self._doc(params)
        if doc is None:
            return None
        line_1, col_1 = position_from_lsp(params.get("position") or {}, doc.text, self.encoding)
        info = self._call_context(doc.text, line_1, col_1)
        if info is None:
            return None
        name, active_param = info
        label = None
        documentation = ""
        builtin = lookup_builtin(name)
        if builtin:
            label, documentation, _cat = builtin
        else:
            sym = self.index.find_function(uri, name)
            if sym is not None:
                label = f"{sym.name}({', '.join(sym.params)})"
                documentation = sym.doc
        if not label:
            return None
        return {
            "signatures": [
                {
                    "label": label,
                    "documentation": documentation,
                    "parameters": _params_from_signature(label),
                }
            ],
            "activeSignature": 0,
            "activeParameter": max(0, active_param),
        }

    def _call_context(self, text: str, line_1: int, col_1: int) -> tuple[str, int] | None:
        try:
            tokens = tokenize(text)
        except DSLError:
            return None
        stack = 0
        active = 0
        callee = None
        for index, token in enumerate(tokens):
            after = token.line > line_1 or (token.line == line_1 and token.col >= col_1)
            if after:
                break
            if token.type == T_OP and token.value == "(":
                prev = tokens[index - 1] if index else None
                stack += 1
                if prev is not None and prev.type == T_NAME:
                    callee = prev.value
                    active = 0
            elif token.type == T_OP and token.value == ")":
                stack = max(0, stack - 1)
            elif token.type == T_OP and token.value == "," and stack > 0:
                active += 1
        if callee is None:
            return None
        return callee, active

    # -- helpers --------------------------------------------------------

    def _doc(self, params: dict) -> tuple[str, Document | None]:
        item = params.get("textDocument") or {}
        uri = normalize_uri(item.get("uri", ""))
        return uri, self.workspace.get(uri)

    def _hit(self, params: dict) -> tuple[str, Document, Token] | None:
        uri, doc = self._doc(params)
        if doc is None:
            return None
        line_1, col_1 = position_from_lsp(params.get("position") or {}, doc.text, self.encoding)
        token = self._token_at(doc.text, line_1, col_1)
        if token is None:
            return None
        return uri, doc, token

    def _token_at(self, text: str, line_1: int, col_1: int) -> Token | None:
        try:
            tokens = tokenize(text)
        except DSLError:
            return None
        inside: Token | None = None
        at_end: Token | None = None
        for token in tokens:
            if token.type in SKIP_TOKEN_TYPES:
                continue
            if token.line != line_1:
                continue
            length = token_length(token.value, token.type) or len(token.value) or 1
            start = token.col
            end = token.col + length
            if start <= col_1 < end:
                inside = token
                break
            if col_1 == end:
                at_end = token
        return inside if inside is not None else at_end

    def _program(self, uri: str, text: str):
        entry = self.index.files.get(uri)
        if entry is not None and entry.program is not None and entry.text == text:
            return entry.program
        try:
            return parse(text)
        except DSLError:
            return None

    def _text_of(self, uri: str, path: Path) -> str:
        doc = self.workspace.get(uri)
        if doc is not None:
            return doc.text
        entry = self.index.files.get(uri)
        if entry is not None:
            return entry.text
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return ""

    def _display_path(self, path: Path) -> str:
        root = self.root
        try:
            if root is not None:
                return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            pass
        return relative_display(path, root)

    def _spec_for(self, uri: str) -> PuzzleSpec | None:
        path = uri_to_path(uri)
        if path.suffix != ".dsl":
            return None
        meta = path.with_suffix(".json")
        if not meta.is_file():
            return None
        # Library files live next to no json; impls/*.dsl do.
        if path.parent.name != "impls":
            return None
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            return PuzzleSpec.from_json(data, source=self.workspace.text(uri) or "")
        except Exception:
            return None

    def _json_for(self, uri: str) -> Path | None:
        path = uri_to_path(uri).with_suffix(".json")
        return path if path.is_file() else None

    def _sample_for(self, uri: str, key: str):
        from puzzle.spec import Instance, SAMPLES_DIR

        path = uri_to_path(uri)
        candidates = [
            path.parent / "samples" / f"{key}.json",
            SAMPLES_DIR / f"{key}.json",
        ]
        for candidate in candidates:
            if candidate.is_file():
                try:
                    return Instance.from_json(json.loads(candidate.read_text(encoding="utf-8")))
                except Exception:
                    continue
        return None

    def _variables_for(self, uri: str) -> tuple[VarSpec, ...]:
        spec = self._spec_for(uri)
        if spec is None:
            return ()
        return spec.variables


def _mod(name: str) -> int:
    return 1 << _MOD_INDEX[name]


def _root_from_init(params: dict) -> Path | None:
    folders = params.get("workspaceFolders")
    if folders:
        uri = folders[0].get("uri")
        if uri:
            return uri_to_path(uri)
    uri = params.get("rootUri")
    if uri:
        return uri_to_path(uri)
    root = params.get("rootPath")
    if root:
        return Path(root)
    return Path.cwd()


def _find_json_var(text: str, name: str) -> tuple[int, int, int] | None:
    anchor = text.find('"variables"')
    if anchor < 0:
        return None
    pattern = re.compile(r'"name"\s*:\s*"(' + re.escape(name) + r')"')
    match = pattern.search(text, anchor)
    if match is None:
        return None
    start = match.start(1)
    line = text.count("\n", 0, start) + 1
    last_nl = text.rfind("\n", 0, start)
    col = start - last_nl
    return line, col, len(name)


def _params_from_signature(label: str) -> list[dict]:
    if "(" not in label or not label.endswith(")"):
        return []
    inner = label[label.find("(") + 1 : -1].strip()
    if not inner or inner == "...":
        return []
    return [{"label": part.strip()} for part in inner.split(",") if part.strip()]


def _unique_locations(items: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    out: list[dict] = []
    for item in items:
        key = (
            item.get("uri"),
            (item.get("range") or {}).get("start", {}).get("line"),
            (item.get("range") or {}).get("start", {}).get("character"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


_HANDLERS = {
    "initialize": LanguageServer.initialize,
    "initialized": LanguageServer.initialized,
    "shutdown": LanguageServer.shutdown,
    "exit": LanguageServer.exit,
    "textDocument/didOpen": LanguageServer.did_open,
    "textDocument/didChange": LanguageServer.did_change,
    "textDocument/didSave": LanguageServer.did_save,
    "textDocument/didClose": LanguageServer.did_close,
    "workspace/didChangeConfiguration": LanguageServer.did_change_configuration,
    "workspace/didChangeWatchedFiles": LanguageServer.did_change_watched_files,
    "textDocument/semanticTokens/full": LanguageServer.semantic_tokens,
    "textDocument/hover": LanguageServer.hover,
    "textDocument/definition": LanguageServer.definition,
    "textDocument/references": LanguageServer.references,
    "textDocument/documentSymbol": LanguageServer.document_symbol,
    "workspace/symbol": LanguageServer.workspace_symbol,
    "textDocument/completion": LanguageServer.completion,
    "textDocument/signatureHelp": LanguageServer.signature_help,
}

_NOTIFICATIONS = {
    "initialized",
    "exit",
    "textDocument/didOpen",
    "textDocument/didChange",
    "textDocument/didSave",
    "textDocument/didClose",
    "workspace/didChangeConfiguration",
    "workspace/didChangeWatchedFiles",
}


def main() -> None:
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    server = LanguageServer()
    rpc = Rpc(stdin, stdout)
    server.rpc = rpc
    try:
        rpc.listen(server.dispatch)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"puzzle-dsl-lsp crashed: {exc}\n")
        raise
    sys.exit(0 if server.shutdown_requested else 1)
