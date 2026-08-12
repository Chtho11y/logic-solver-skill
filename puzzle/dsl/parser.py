"""Recursive-descent parser for the puzzle DSL.

Grammar (informal EBNF)::

    program     := { NEWLINE } { statement }
    statement   := simple NEWLINE | compound
    compound    := if_stmt | for_stmt
    if_stmt     := 'if' expr ':' suite ['else' ':' suite]
    for_stmt    := 'for' NAME {',' NAME} 'in' expr ':' suite
    suite       := simple NEWLINE | NEWLINE INDENT statement+ DEDENT
    simple      := 'let' NAME {',' NAME} '=' expr | expr
    expr        := implies_expr
    implies_expr:= or_expr ['=>' implies_expr]
    or_expr     := xor_expr {('or'|'||') xor_expr}
    xor_expr    := and_expr {'^' and_expr}
    and_expr    := not_expr {('and'|'&&') not_expr}
    not_expr    := ('not'|'!') not_expr | comparison
    comparison  := arith {('=='|'!='|'<'|'<='|'>'|'>=') arith}
    arith       := term {('+'|'-') term}
    term        := factor {('*'|'/'|'%') factor}
    factor      := ('+'|'-') factor | postfix
    postfix     := primary {'[' expr ']' | '(' [args] ')' | '.' NAME}
    primary     := INT | 'true' | 'false' | NAME | '(' expr ')' | '[' [items] ']'

UI-independent (no PyQt import).
"""

from __future__ import annotations

from . import ast_nodes as ast
from .errors import ParseError
from .lexer import tokenize
from .tokens import (
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

_COMPARISON_OPS = frozenset({"==", "!=", "<", "<=", ">", ">="})


def parse(source: str) -> ast.Program:
    """Parse ``source`` into a :class:`~ast_nodes.Program`."""

    return _Parser(tokenize(source)).parse_program()

class _Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    # -- token helpers --------------------------------------------------

    @property
    def _cur(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        token = self._tokens[self._pos]
        if token.type != T_EOF:
            self._pos += 1
        return token

    def _check(self, ttype: str, value: str | None = None) -> bool:
        token = self._cur
        if token.type != ttype:
            return False
        return value is None or token.value == value

    def _accept(self, ttype: str, value: str | None = None) -> Token | None:
        if self._check(ttype, value):
            return self._advance()
        return None

    def _expect(self, ttype: str, value: str | None = None) -> Token:
        if not self._check(ttype, value):
            want = value if value is not None else ttype
            got = self._cur.value or self._cur.type
            raise ParseError(f"expected {want!r} but found {got!r}", self._cur.line, self._cur.col)
        return self._advance()

    def _skip_newlines(self) -> None:
        while self._check(T_NEWLINE):
            self._advance()

    # -- grammar --------------------------------------------------------

    def parse_program(self) -> ast.Program:
        self._skip_newlines()
        statements: list[ast.Stmt] = []
        while not self._check(T_EOF):
            statements.append(self._statement())
            self._skip_newlines()
        return ast.Program(statements=statements)

    def _statement(self) -> ast.Stmt:
        if self._check(T_KEYWORD, "if"):
            return self._if_stmt()
        if self._check(T_KEYWORD, "for"):
            return self._for_stmt()
        if self._check(T_KEYWORD, "def"):
            return self._def_stmt()
        stmt = self._simple_stmt()
        if not self._check(T_EOF):
            self._expect(T_NEWLINE)
        return stmt

    def _def_stmt(self) -> ast.DefStmt:
        kw = self._expect(T_KEYWORD, "def")
        name = self._expect(T_NAME).value
        self._expect(T_OP, "(")
        params: list[str] = []
        if not self._check(T_OP, ")"):
            params.append(self._expect(T_NAME).value)
            while self._accept(T_OP, ","):
                params.append(self._expect(T_NAME).value)
        self._expect(T_OP, ")")
        self._expect(T_OP, ":")
        body = self._suite()
        return ast.DefStmt(line=kw.line, col=kw.col, name=name, params=params, body=body)

    def _if_stmt(self) -> ast.IfStmt:
        kw = self._expect(T_KEYWORD, "if")
        return self._if_tail(kw)

    def _if_tail(self, kw: Token) -> ast.IfStmt:
        cond = self._expression()
        self._expect(T_OP, ":")
        body = self._suite()
        orelse: list[ast.Stmt] = []
        if self._check(T_KEYWORD, "elif"):
            tok = self._advance()
            orelse = [self._if_tail(tok)]
        elif self._check(T_KEYWORD, "else"):
            self._advance()
            self._expect(T_OP, ":")
            orelse = self._suite()
        return ast.IfStmt(line=kw.line, col=kw.col, cond=cond, body=body, orelse=orelse)

    def _for_stmt(self) -> ast.ForStmt:
        kw = self._expect(T_KEYWORD, "for")
        names = self._name_list()
        self._expect(T_KEYWORD, "in")
        iterable = self._expression()
        self._expect(T_OP, ":")
        body = self._suite()
        return ast.ForStmt(line=kw.line, col=kw.col, vars=names, iterable=iterable, body=body)

    def _name_list(self) -> list[str]:
        """Parse one or more comma-separated target names."""

        names = [self._expect(T_NAME).value]
        while self._accept(T_OP, ","):
            names.append(self._expect(T_NAME).value)
        return names

    def _suite(self) -> list[ast.Stmt]:
        # Inline single statement: `if cond: stmt`
        if not self._check(T_NEWLINE):
            stmt = self._simple_stmt()
            if not self._check(T_EOF):
                self._expect(T_NEWLINE)
            return [stmt]
        # Block: NEWLINE INDENT statement+ DEDENT
        self._expect(T_NEWLINE)
        self._expect(T_INDENT)
        statements: list[ast.Stmt] = []
        while not self._check(T_DEDENT) and not self._check(T_EOF):
            statements.append(self._statement())
            self._skip_newlines()
        self._expect(T_DEDENT)
        if not statements:
            raise ParseError("expected an indented block", self._cur.line, self._cur.col)
        return statements

    def _simple_stmt(self) -> ast.Stmt:
        if self._check(T_KEYWORD, "let"):
            kw = self._advance()
            targets = self._name_list()
            self._expect(T_OP, "=")
            expr = self._expression()
            return ast.LetStmt(line=kw.line, col=kw.col, targets=targets, expr=expr)
        if self._check(T_KEYWORD, "return"):
            kw = self._advance()
            expr = None
            if not self._check(T_NEWLINE) and not self._check(T_EOF):
                expr = self._expression()
            return ast.ReturnStmt(line=kw.line, col=kw.col, expr=expr)
        if self._check(T_KEYWORD, "import"):
            kw = self._advance()
            path = self._expect(T_STR).value
            return ast.ImportStmt(line=kw.line, col=kw.col, path=path)
        expr = self._expression()
        return ast.ExprStmt(line=expr.line, col=expr.col, expr=expr)

    # -- expressions ----------------------------------------------------

    def _expression(self) -> ast.Expr:
        return self._implies_expr()

    def _implies_expr(self) -> ast.Expr:
        left = self._or_expr()
        if self._check(T_OP, "=>"):
            op = self._advance()
            # Right-associative: a => b => c parses as a => (b => c).
            right = self._implies_expr()
            return ast.Binary(line=op.line, col=op.col, op="implies", left=left, right=right)
        return left

    def _or_expr(self) -> ast.Expr:
        left = self._xor_expr()
        while self._check(T_KEYWORD, "or") or self._check(T_OP, "||"):
            op = self._advance()
            right = self._xor_expr()
            left = ast.Binary(line=op.line, col=op.col, op="or", left=left, right=right)
        return left

    def _xor_expr(self) -> ast.Expr:
        left = self._and_expr()
        while self._check(T_OP, "^"):
            op = self._advance()
            right = self._and_expr()
            left = ast.Binary(line=op.line, col=op.col, op="xor", left=left, right=right)
        return left

    def _and_expr(self) -> ast.Expr:
        left = self._not_expr()
        while self._check(T_KEYWORD, "and") or self._check(T_OP, "&&"):
            op = self._advance()
            right = self._not_expr()
            left = ast.Binary(line=op.line, col=op.col, op="and", left=left, right=right)
        return left

    def _not_expr(self) -> ast.Expr:
        if self._check(T_KEYWORD, "not") or self._check(T_OP, "!"):
            op = self._advance()
            operand = self._not_expr()
            return ast.Unary(line=op.line, col=op.col, op="not", operand=operand)
        return self._comparison()

    def _comparison(self) -> ast.Expr:
        left = self._arith()
        while self._cur.type == T_OP and self._cur.value in _COMPARISON_OPS:
            op = self._advance()
            right = self._arith()
            left = ast.Binary(line=op.line, col=op.col, op=op.value, left=left, right=right)
        return left

    def _arith(self) -> ast.Expr:
        left = self._term()
        while self._cur.type == T_OP and self._cur.value in ("+", "-"):
            op = self._advance()
            right = self._term()
            left = ast.Binary(line=op.line, col=op.col, op=op.value, left=left, right=right)
        return left

    def _term(self) -> ast.Expr:
        left = self._factor()
        while self._cur.type == T_OP and self._cur.value in ("*", "/", "%"):
            op = self._advance()
            right = self._factor()
            left = ast.Binary(line=op.line, col=op.col, op=op.value, left=left, right=right)
        return left

    def _factor(self) -> ast.Expr:
        if self._cur.type == T_OP and self._cur.value in ("+", "-"):
            op = self._advance()
            operand = self._factor()
            return ast.Unary(line=op.line, col=op.col, op=op.value, operand=operand)
        return self._postfix()

    def _postfix(self) -> ast.Expr:
        node = self._primary()
        while True:
            if self._check(T_OP, "["):
                tok = self._advance()
                index = self._expression()
                self._expect(T_OP, "]")
                node = ast.Index(line=tok.line, col=tok.col, base=node, index=index)
            elif self._check(T_OP, "("):
                tok = self._advance()
                args = self._call_args()
                self._expect(T_OP, ")")
                node = ast.Call(line=tok.line, col=tok.col, callee=node, args=args)
            elif self._check(T_OP, "."):
                tok = self._advance()
                attr = self._expect(T_NAME)
                node = ast.Member(line=tok.line, col=tok.col, base=node, attr=attr.value)
            else:
                break
        return node

    def _call_args(self) -> list[ast.Expr]:
        args: list[ast.Expr] = []
        if self._check(T_OP, ")"):
            return args
        args.append(self._expression())
        while self._accept(T_OP, ","):
            args.append(self._expression())
        return args

    def _primary(self) -> ast.Expr:
        token = self._cur
        if token.type == T_INT:
            self._advance()
            return ast.Num(line=token.line, col=token.col, value=int(token.value))
        if token.type == T_STR:
            self._advance()
            return ast.Str(line=token.line, col=token.col, value=token.value)
        if token.type == T_KEYWORD and token.value in ("true", "false"):
            self._advance()
            return ast.Bool(line=token.line, col=token.col, value=token.value == "true")
        if token.type == T_NAME:
            self._advance()
            return ast.Name(line=token.line, col=token.col, ident=token.value)
        if self._check(T_OP, "("):
            self._advance()
            expr = self._expression()
            self._expect(T_OP, ")")
            return expr
        if self._check(T_OP, "["):
            tok = self._advance()
            items: list[ast.Expr] = []
            if not self._check(T_OP, "]"):
                items.append(self._expression())
                while self._accept(T_OP, ","):
                    items.append(self._expression())
            self._expect(T_OP, "]")
            return ast.ListLit(line=tok.line, col=tok.col, items=items)
        raise ParseError(f"unexpected token {token.value or token.type!r}", token.line, token.col)
