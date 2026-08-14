"""Abstract syntax tree node definitions for the puzzle DSL.

UI-independent (no PyQt import). Every node carries ``line``/``col`` for error
reporting during compilation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


@dataclass
class Node:
    line: int = 0
    col: int = 0


# -- expressions --------------------------------------------------------------


@dataclass
class Num(Node):
    value: int = 0


@dataclass
class Bool(Node):
    value: bool = False


@dataclass
class Str(Node):
    value: str = ""


@dataclass
class Name(Node):
    ident: str = ""


@dataclass
class ListLit(Node):
    items: list["Expr"] = field(default_factory=list)


@dataclass
class Index(Node):
    base: "Expr" = None  # type: ignore[assignment]
    index: "Expr" = None  # type: ignore[assignment]


@dataclass
class Member(Node):
    """Attribute access ``base.attr`` (e.g. ``x.cc`` / ``x.cc.id``)."""

    base: "Expr" = None  # type: ignore[assignment]
    attr: str = ""


@dataclass
class Call(Node):
    callee: "Expr" = None  # type: ignore[assignment]
    args: list["Expr"] = field(default_factory=list)


@dataclass
class Unary(Node):
    op: str = ""
    operand: "Expr" = None  # type: ignore[assignment]


@dataclass
class Binary(Node):
    op: str = ""
    left: "Expr" = None  # type: ignore[assignment]
    right: "Expr" = None  # type: ignore[assignment]


@dataclass
class Lambda(Node):
    """``fn (a, b) -> expr`` — anonymous function with a captured scope."""

    params: list[str] = field(default_factory=list)
    body: "Expr" = None  # type: ignore[assignment]


Expr = Union[Num, Bool, Str, Name, ListLit, Index, Member, Call, Unary, Binary, Lambda]


# -- statements ---------------------------------------------------------------


@dataclass
class LetStmt(Node):
    # ``targets`` holds one name for ``let x = ...`` or several for the
    # structured binding ``let a, b, c = ...``.
    targets: list[str] = field(default_factory=list)
    expr: "Expr" = None  # type: ignore[assignment]


@dataclass
class ExprStmt(Node):
    expr: "Expr" = None  # type: ignore[assignment]


@dataclass
class IfStmt(Node):
    cond: "Expr" = None  # type: ignore[assignment]
    body: list["Stmt"] = field(default_factory=list)
    orelse: list["Stmt"] = field(default_factory=list)


@dataclass
class ForStmt(Node):
    # ``vars`` holds one name for ``for x in ...`` or several for the
    # structured binding ``for a, b, c in ...``.
    vars: list[str] = field(default_factory=list)
    iterable: "Expr" = None  # type: ignore[assignment]
    body: list["Stmt"] = field(default_factory=list)


@dataclass
class DefStmt(Node):
    """``def name(a, b): body`` -- a reusable, compile-time-inlined helper."""

    name: str = ""
    params: list[str] = field(default_factory=list)
    body: list["Stmt"] = field(default_factory=list)
    # Location of the function *name* (not the ``def`` keyword). Optional so
    # older constructed nodes remain valid; 0 means "fall back to line/col".
    name_line: int = 0
    name_col: int = 0


@dataclass
class ReturnStmt(Node):
    """``return expr`` -- ends the enclosing ``def`` with a value."""

    expr: "Expr" = None  # type: ignore[assignment]


@dataclass
class ImportStmt(Node):
    """``import "lib/connect"`` -- inline another DSL module's definitions."""

    path: str = ""


@dataclass
class MetaStmt(Node):
    """``meta: body`` -- sequential compile-time solving (see META_SOLVE_PLAN)."""

    body: list["Stmt"] = field(default_factory=list)


@dataclass
class ScopeStmt(Node):
    """``scope: body`` -- solver push/pop; does not introduce a DSL scope."""

    body: list["Stmt"] = field(default_factory=list)


Stmt = Union[
    LetStmt, ExprStmt, IfStmt, ForStmt, DefStmt, ReturnStmt, ImportStmt, MetaStmt, ScopeStmt
]


@dataclass
class Program(Node):
    statements: list["Stmt"] = field(default_factory=list)
    # Set by the loader so error messages can name the originating module.
    module: str = ""
