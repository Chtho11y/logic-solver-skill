"""Cross-file symbol index for the puzzle DSL.

Built from ``parse()`` only — no z3, no puzzle instance. A file that fails to
parse keeps its last successful index entry so go-to-definition still works
while the user is mid-edit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from puzzle.dsl import ast_nodes as ast
from puzzle.dsl.errors import DSLError
from puzzle.dsl.parser import parse
from puzzle.spec import IMPLS_DIR, LIB_DIR

from .convert import path_to_uri, uri_to_path
from .docs import extract_def_doc


@dataclass
class Symbol:
    name: str
    params: list[str]
    uri: str
    line: int
    col: int
    module: str
    doc: str
    nested: bool = False
    end_line: int = 0


@dataclass
class ImportRef:
    name: str
    line: int
    col: int
    str_col: int


@dataclass
class FileEntry:
    uri: str
    path: Path
    text: str
    symbols: list[Symbol] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    import_refs: list[ImportRef] = field(default_factory=list)
    program: ast.Program | None = None
    ok: bool = True


def resolve_module(name: str, search: list[Path]) -> Path | None:
    """Mirror ``make_loader``: look up ``name`` under lib then impls, no escape."""

    rel = name if name.endswith(".dsl") else f"{name}.dsl"
    for base in search:
        try:
            resolved_base = base.resolve()
        except OSError:
            continue
        candidate = (resolved_base / rel).resolve()
        try:
            if candidate.is_file() and resolved_base in candidate.parents:
                return candidate
        except OSError:
            continue
    return None


def search_dirs(root: Path | None) -> list[Path]:
    dirs: list[Path] = []
    seen: set[Path] = set()
    candidates: list[Path] = []
    if root is not None:
        candidates.extend([root / "puzzle" / "lib", root / "impls"])
    candidates.extend([LIB_DIR, IMPLS_DIR])
    for path in candidates:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved.is_dir() and resolved not in seen:
            seen.add(resolved)
            dirs.append(resolved)
    return dirs


def node_end_line(node) -> int:
    end = int(getattr(node, "line", 0) or 0)
    for value in _child_nodes(node):
        end = max(end, node_end_line(value))
    return end


def _child_nodes(node):
    if isinstance(node, ast.Program):
        yield from node.statements
    elif isinstance(node, ast.DefStmt):
        yield from node.body
    elif isinstance(node, ast.IfStmt):
        yield node.cond
        yield from node.body
        yield from node.orelse
    elif isinstance(node, ast.ForStmt):
        yield node.iterable
        yield from node.body
    elif isinstance(node, ast.LetStmt):
        yield node.expr
    elif isinstance(node, ast.ExprStmt):
        yield node.expr
    elif isinstance(node, ast.ReturnStmt) and node.expr is not None:
        yield node.expr
    elif isinstance(node, ast.Call):
        yield node.callee
        yield from node.args
    elif isinstance(node, ast.Binary):
        yield node.left
        yield node.right
    elif isinstance(node, ast.Unary):
        yield node.operand
    elif isinstance(node, ast.Index):
        yield node.base
        yield node.index
    elif isinstance(node, ast.Member):
        yield node.base
    elif isinstance(node, ast.ListLit):
        yield from node.items
    elif isinstance(node, ast.Lambda):
        yield node.body
    elif isinstance(node, ast.MetaStmt):
        yield from node.body
    elif isinstance(node, ast.ScopeStmt):
        yield from node.body


def walk_nodes(node):
    yield node
    for child in _child_nodes(node):
        yield from walk_nodes(child)


def iter_defs(stmts, nested: bool = False):
    for stmt in stmts:
        if isinstance(stmt, ast.DefStmt):
            yield stmt, nested
            yield from iter_defs(stmt.body, nested=True)
        elif isinstance(stmt, ast.IfStmt):
            yield from iter_defs(stmt.body, nested)
            yield from iter_defs(stmt.orelse, nested)
        elif isinstance(stmt, ast.ForStmt):
            yield from iter_defs(stmt.body, nested)


@dataclass
class LocalBinding:
    name: str
    line: int
    col: int
    kind: str  # param | let | for


def locals_covering(program: ast.Program, line: int) -> dict[str, LocalBinding]:
    """Bindings visible at ``line``, innermost winning (compiler scope stack)."""

    best: dict[str, LocalBinding] = {}
    best_depth = -1

    def apply_lets(stmts, acc: dict[str, LocalBinding]) -> None:
        for stmt in stmts:
            if isinstance(stmt, ast.LetStmt) and stmt.line <= line:
                for name in stmt.targets:
                    acc[name] = LocalBinding(name, stmt.line, stmt.col, "let")

    def consider(acc: dict[str, LocalBinding], depth: int) -> None:
        nonlocal best, best_depth
        if depth >= best_depth:
            best_depth = depth
            best = dict(acc)

    def walk(stmts, acc: dict[str, LocalBinding], depth: int) -> None:
        current = dict(acc)
        apply_lets(stmts, current)
        consider(current, depth)
        for stmt in stmts:
            if isinstance(stmt, ast.DefStmt):
                end = node_end_line(stmt)
                if stmt.line <= line <= end:
                    inner = dict(current)
                    name_line = stmt.name_line or stmt.line
                    name_col = stmt.name_col or stmt.col
                    for param in stmt.params:
                        inner[param] = LocalBinding(param, name_line, name_col, "param")
                    walk(stmt.body, inner, depth + 1)
            elif isinstance(stmt, ast.ForStmt):
                end = node_end_line(stmt)
                if stmt.line <= line <= end:
                    inner = dict(current)
                    for name in stmt.vars:
                        inner[name] = LocalBinding(name, stmt.line, stmt.col, "for")
                    walk(stmt.body, inner, depth + 1)
            elif isinstance(stmt, ast.IfStmt):
                end = node_end_line(stmt)
                if stmt.line <= line <= end:
                    walk(stmt.body, dict(current), depth + 1)
                    walk(stmt.orelse, dict(current), depth + 1)

    walk(program.statements, {}, 0)
    return best


def collect_let_for_lines(program: ast.Program) -> dict[int, set[str]]:
    """Map a source line to names bound by ``let`` / ``for`` on that line."""

    out: dict[int, set[str]] = {}
    for node in walk_nodes(program):
        if isinstance(node, ast.LetStmt):
            out.setdefault(node.line, set()).update(node.targets)
        elif isinstance(node, ast.ForStmt):
            out.setdefault(node.line, set()).update(node.vars)
    return out


def enclosing_def_params(program: ast.Program, line: int) -> set[str]:
    best: set[str] = set()
    best_span = None
    for stmt, _nested in iter_defs(program.statements):
        end = node_end_line(stmt)
        if stmt.line <= line <= end:
            span = end - stmt.line
            if best_span is None or span <= best_span:
                best_span = span
                best = set(stmt.params)
    return best


class Index:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root
        self.search = search_dirs(root)
        self.files: dict[str, FileEntry] = {}
        self.reverse: dict[str, set[str]] = {}

    def build(self) -> None:
        for folder in self.search:
            try:
                paths = sorted(folder.glob("*.dsl"))
            except OSError:
                continue
            for path in paths:
                self.index_path(path)

    def index_path(self, path: Path, text: str | None = None) -> FileEntry | None:
        try:
            path = path.resolve()
        except OSError:
            return None
        if not path.is_file() and text is None:
            return None
        source = text if text is not None else path.read_text(encoding="utf-8")
        uri = path_to_uri(path)
        return self._index_source(uri, path, source)

    def index_uri(self, uri: str, text: str, path: Path | None = None) -> FileEntry:
        resolved = path if path is not None else uri_to_path(uri)
        try:
            resolved = resolved.resolve()
        except OSError:
            pass
        return self._index_source(uri, resolved, text)

    def drop(self, uri: str) -> None:
        entry = self.files.pop(uri, None)
        if entry is None:
            return
        self._unlink_imports(uri, entry.imports)

    def _index_source(self, uri: str, path: Path, source: str) -> FileEntry:
        previous = self.files.get(uri)
        try:
            program = parse(source)
        except DSLError:
            if previous is not None:
                previous.text = source
                previous.ok = False
                return previous
            entry = FileEntry(uri=uri, path=path, text=source, ok=False)
            self.files[uri] = entry
            return entry
        except Exception:
            if previous is not None:
                previous.text = source
                previous.ok = False
                return previous
            entry = FileEntry(uri=uri, path=path, text=source, ok=False)
            self.files[uri] = entry
            return entry

        if previous is not None:
            self._unlink_imports(uri, previous.imports)

        module = path.stem
        symbols: list[Symbol] = []
        for stmt, nested in iter_defs(program.statements):
            line = stmt.name_line or stmt.line
            col = stmt.name_col or stmt.col
            symbols.append(
                Symbol(
                    name=stmt.name,
                    params=list(stmt.params),
                    uri=uri,
                    line=line,
                    col=col,
                    module=module,
                    doc=extract_def_doc(source, stmt.line),
                    nested=nested,
                    end_line=node_end_line(stmt),
                )
            )
        imports: list[str] = []
        import_refs: list[ImportRef] = []
        for node in walk_nodes(program):
            if isinstance(node, ast.ImportStmt):
                imports.append(node.path)
                import_refs.append(ImportRef(name=node.path, line=node.line, col=node.col, str_col=0))

        entry = FileEntry(
            uri=uri,
            path=path,
            text=source,
            symbols=symbols,
            imports=imports,
            import_refs=import_refs,
            program=program,
            ok=True,
        )
        self.files[uri] = entry
        self._link_imports(uri, imports)
        return entry

    def _unlink_imports(self, uri: str, names: list[str]) -> None:
        for name in names:
            target = resolve_module(name, self.search)
            if target is None:
                continue
            bucket = self.reverse.get(path_to_uri(target))
            if bucket:
                bucket.discard(uri)

    def _link_imports(self, uri: str, names: list[str]) -> None:
        for name in names:
            target = resolve_module(name, self.search)
            if target is None:
                continue
            self.reverse.setdefault(path_to_uri(target), set()).add(uri)

    def dependents(self, uri: str) -> set[str]:
        return set(self.reverse.get(uri, ()))

    def top_level(self, uri: str) -> list[Symbol]:
        entry = self.files.get(uri)
        if entry is None:
            return []
        return [sym for sym in entry.symbols if not sym.nested]

    def all_symbols(self) -> list[Symbol]:
        out: list[Symbol] = []
        for entry in self.files.values():
            out.extend(sym for sym in entry.symbols if not sym.nested)
        return out

    def visible_functions(self, uri: str) -> dict[str, Symbol]:
        """Name → symbol, matching compiler hoist-then-import overwrite order."""

        entry = self.files.get(uri)
        if entry is None:
            return {}
        out: dict[str, Symbol] = {}
        for sym in entry.symbols:
            if not sym.nested:
                out[sym.name] = sym
        seen: set[str] = set()

        def apply_import(name: str) -> None:
            if name in seen:
                return
            seen.add(name)
            path = resolve_module(name, self.search)
            if path is None:
                return
            imported = self.files.get(path_to_uri(path))
            if imported is None:
                imported = self.index_path(path)
            if imported is None:
                return
            for sym in imported.symbols:
                if not sym.nested:
                    out[sym.name] = sym
            for child in imported.imports:
                apply_import(child)

        for name in entry.imports:
            apply_import(name)
        return out

    def find_function(self, uri: str, name: str) -> Symbol | None:
        return self.visible_functions(uri).get(name)
