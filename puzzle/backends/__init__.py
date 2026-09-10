"""Solver backend abstraction and cspuz implementation."""

from .base import (
    BackendError,
    BackendInfo,
    BackendTimeoutError,
    BackendUnavailableError,
    BackendUnknownError,
    ConstraintModel,
)
from .cspuz import CspuzModel, backend_configuration, create_model
from .registry import (
    BACKEND_NAMES,
    backend_info,
    cspuz_available,
    list_backends,
    normalize_backend,
    resolve_backend,
)

__all__ = [
    "BACKEND_NAMES",
    "BackendError",
    "BackendInfo",
    "BackendTimeoutError",
    "BackendUnavailableError",
    "BackendUnknownError",
    "ConstraintModel",
    "CspuzModel",
    "backend_configuration",
    "backend_info",
    "create_model",
    "cspuz_available",
    "list_backends",
    "normalize_backend",
    "resolve_backend",
]
