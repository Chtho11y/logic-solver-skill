"""Solver backend abstraction and cspuz implementation."""

from .base import (
    BackendError,
    BackendInfo,
    BackendTimeoutError,
    BackendUnavailableError,
    BackendUnknownError,
    ConstraintModel,
)
from .features import (
    FEATURE_GRAPH_DIVISION,
    FEATURE_GRAPH_EDGE_PATH,
    FEATURE_GRAPH_VERTEX_CONNECTED,
    FEATURE_TIMEOUT,
    BackendFeatures,
    backends_with_feature,
    features_for,
)
from .cspuz import CspuzModel, backend_configuration, create_model
from .registry import (
    BACKEND_NAMES,
    backend_info,
    cspuz_available,
    effective_timeout_ms,
    list_backends,
    merge_backend_request,
    normalize_backend,
    resolve_backend,
)

__all__ = [
    "BACKEND_NAMES",
    "BackendError",
    "BackendFeatures",
    "BackendInfo",
    "BackendTimeoutError",
    "BackendUnavailableError",
    "BackendUnknownError",
    "ConstraintModel",
    "CspuzModel",
    "FEATURE_GRAPH_DIVISION",
    "FEATURE_GRAPH_EDGE_PATH",
    "FEATURE_GRAPH_VERTEX_CONNECTED",
    "FEATURE_TIMEOUT",
    "backend_configuration",
    "backend_info",
    "backends_with_feature",
    "create_model",
    "cspuz_available",
    "effective_timeout_ms",
    "features_for",
    "list_backends",
    "merge_backend_request",
    "normalize_backend",
    "resolve_backend",
]
