"""Grid-puzzle solving toolkit: geometry model, constraint DSL and runner."""

from __future__ import annotations

from .grid import Grid
from .models import Point, PointKind, Region, Variable, VarType

__all__ = ["Grid", "Point", "PointKind", "Region", "Variable", "VarType"]
