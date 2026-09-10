"""Puzzle DSL: lexer + parser + AST -> cspuz compiler and solver.

The DSL describes grid-puzzle constraints lowered through a neutral model API:

* types: numbers, booleans, variables (a region's quantity set), regions
  (cell / edge / corner) and lists;
* ``x[region]`` extracts a variable's quantities over a region;
* ``if cond: body`` -> ``Implies``; ``for v in list: body`` unrolls;
* predefined functions (single-element functions map over lists) and automatic
  broadcasting between lists/elements.

UI-independent (no PyQt import). Concrete solvers are selected through cspuz.
"""

from __future__ import annotations

from .builtins import DocEntry, function_table
from .errors import CompileError, DSLError, LexError, ParseError
from .parser import parse
from .solver import (
    SOLVER_BACKENDS,
    SOLVER_LOGICS,
    STATUS_COMPILED,
    STATUS_ERROR,
    STATUS_SAT,
    STATUS_UNKNOWN,
    STATUS_UNSAT,
    SolveResult,
    backend_status,
    compile_only,
    format_model,
    is_available,
    solve,
)

__all__ = [
    "parse",
    "function_table",
    "DocEntry",
    "solve",
    "compile_only",
    "SOLVER_BACKENDS",
    "SOLVER_LOGICS",
    "is_available",
    "backend_status",
    "format_model",
    "SolveResult",
    "STATUS_SAT",
    "STATUS_UNSAT",
    "STATUS_UNKNOWN",
    "STATUS_ERROR",
    "STATUS_COMPILED",
    "DSLError",
    "LexError",
    "ParseError",
    "CompileError",
]
