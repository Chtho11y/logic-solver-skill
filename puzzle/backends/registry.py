"""Discovery and selection for the concrete solvers exposed by cspuz."""

from __future__ import annotations

import importlib
import os
import shutil

from .base import BackendError, BackendInfo, BackendUnavailableError
from .features import features_for

BACKEND_NAMES: tuple[str, ...] = (
    "auto",
    "cspuz_core",
    "z3",
    "csugar",
    "sugar",
    "sugar_extended",
)

_LABELS = {
    "auto": "Auto (timeout-aware)",
    "cspuz_core": "cspuz_core",
    "z3": "Z3",
    "csugar": "csugar",
    "sugar": "Sugar",
    "sugar_extended": "Sugar extended",
}

_ALIASES = {
    "": "auto",
    "auto": "auto",
    "cspuz_core": "cspuz_core",
    "cspuz-core": "cspuz_core",
    "core": "cspuz_core",
    "z3": "z3",
    "csugar": "csugar",
    "sugar": "sugar",
    "sugar-ext": "sugar_extended",
    "sugar_extended": "sugar_extended",
}


def _module_available(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


def cspuz_available() -> bool:
    return _module_available("cspuz")


def _make_info(
    name: str,
    available: bool,
    reason: str = "",
    *,
    supports_timeout: bool | None = None,
    supports_graph_primitives: bool | None = None,
    extra_features: tuple[str, ...] | None = None,
) -> BackendInfo:
    feats = features_for(name)
    timeout = feats.timeout if supports_timeout is None else supports_timeout
    graph = (
        feats.graph_vertex_connected
        if supports_graph_primitives is None
        else supports_graph_primitives
    )
    feature_names = extra_features if extra_features is not None else feats.names()
    return BackendInfo(
        name,
        _LABELS[name],
        available,
        reason,
        timeout,
        graph,
        feature_names,
    )


def _concrete_info(name: str) -> BackendInfo:
    if not cspuz_available():
        return _make_info(
            name, False, "cspuz is not installed; install requirements.txt"
        )

    if name == "cspuz_core":
        ok = _module_available("cspuz_core")
        reason = "" if ok else "Python package cspuz_core is not installed"
        return _make_info(name, ok, reason)
    if name == "z3":
        ok = _module_available("z3")
        reason = "" if ok else "Python package z3-solver is not installed"
        return _make_info(name, ok, reason)
    if name == "csugar":
        ok = _module_available("pycsugar")
        reason = "" if ok else "Python package pycsugar is not installed"
        return _make_info(name, ok, reason)

    if os.name == "nt":
        return _make_info(
            name,
            False,
            "pinned cspuz uses /dev/stdin for Sugar; use WSL or another backend",
        )

    configured = os.environ.get("CSPUZ_BACKEND_PATH")
    if not configured:
        try:
            import cspuz

            configured = cspuz.config.backend_path
        except Exception:
            configured = None
    if configured:
        executable = (
            configured if os.path.isfile(configured) else shutil.which(configured)
        )
    else:
        executable = shutil.which("sugar")
    ok = bool(executable)
    timeout_ok = _module_available("psutil")
    if not ok:
        reason = "set CSPUZ_BACKEND_PATH to a Sugar-compatible executable"
    elif not timeout_ok:
        reason = "timeouts require the optional psutil package"
    else:
        reason = ""
    return _make_info(name, ok, reason, supports_timeout=timeout_ok)


def normalize_backend(name: str | None) -> str:
    key = str(name or "auto").strip().lower()
    try:
        return _ALIASES[key]
    except KeyError as exc:
        valid = ", ".join(BACKEND_NAMES)
        raise BackendError(f"unknown solver backend {name!r}; choose one of: {valid}") from exc


def resolve_backend(
    name: str | None = "auto", *, timeout_ms: int | None = None
) -> str:
    """Return an available concrete backend.

    Auto selection is intentionally deterministic and narrower than cspuz's
    own auto mode: cspuz_core is preferred and Z3 is the portable fallback.
    """

    normalized = normalize_backend(name)
    needs_timeout = timeout_ms is not None and timeout_ms > 0
    if normalized == "auto":
        for candidate in ("cspuz_core", "z3"):
            info = _concrete_info(candidate)
            if info.available and (not needs_timeout or info.supports_timeout):
                return candidate
        if needs_timeout:
            raise BackendUnavailableError(
                "no timeout-capable automatic backend is available; install z3-solver "
                "or call with timeout_ms=None"
            )
        raise BackendUnavailableError(
            "no solver backend is available; install cspuz_core or z3-solver"
        )

    info = _concrete_info(normalized)
    if not info.available:
        raise BackendUnavailableError(
            f"solver backend {normalized!r} is unavailable: {info.reason}"
        )
    if needs_timeout and not info.supports_timeout:
        raise BackendError(
            f"solver backend {normalized!r} does not support timeouts; "
            "call with timeout_ms=None or select z3"
        )
    return normalized


def backend_info(name: str) -> BackendInfo:
    normalized = normalize_backend(name)
    if normalized != "auto":
        return _concrete_info(normalized)
    try:
        resolved = resolve_backend("auto")
    except BackendUnavailableError as exc:
        return _make_info("auto", False, str(exc), extra_features=())
    concrete = _concrete_info(resolved)
    primary_infos = [_concrete_info(candidate) for candidate in ("cspuz_core", "z3")]
    timeout_available = any(
        info.available and info.supports_timeout for info in primary_infos
    )
    return _make_info(
        "auto",
        True,
        "",
        supports_timeout=timeout_available,
        supports_graph_primitives=concrete.supports_graph_primitives,
        extra_features=concrete.features,
    )


def merge_backend_request(*, api: str | None, dsl: str | None) -> str:
    """Combine the API ``backend=`` argument with a DSL ``use`` statement.

    Either side may be omitted or ``auto``. The default is the best available
    backend. Two different explicit names are a conflict.
    """

    api_name = normalize_backend(api)
    dsl_name = normalize_backend(dsl) if dsl else "auto"
    if api_name != "auto" and dsl_name != "auto" and api_name != dsl_name:
        raise BackendError(
            f"backend conflict: DSL `use {dsl_name}` vs request {api_name!r}"
        )
    return dsl_name if dsl_name != "auto" else api_name


def effective_timeout_ms(
    requested: str,
    api_backend: str,
    timeout_ms: int | None,
) -> int | None:
    """Drop a timeout that the chosen backend cannot honour.

    ``auto`` plus a positive timeout still prefers a timeout-capable solver.
    An explicit ``use cspuz_core`` (with API left on auto) keeps that backend
    and ignores the timeout, instead of erroring.
    """

    if timeout_ms is None or timeout_ms <= 0:
        return None
    if requested == "auto":
        return timeout_ms
    info = _concrete_info(requested)
    if info.supports_timeout:
        return timeout_ms
    if normalize_backend(api_backend) == "auto":
        return None
    return timeout_ms


def list_backends() -> tuple[BackendInfo, ...]:
    return tuple(backend_info(name) for name in BACKEND_NAMES)
