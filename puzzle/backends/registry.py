"""Discovery and selection for the concrete solvers exposed by cspuz."""

from __future__ import annotations

import importlib
import os
import shutil

from .base import BackendError, BackendInfo, BackendUnavailableError

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


def _concrete_info(name: str) -> BackendInfo:
    if not cspuz_available():
        return BackendInfo(
            name,
            _LABELS[name],
            False,
            "cspuz is not installed; install requirements.txt",
        )

    if name == "cspuz_core":
        ok = _module_available("cspuz_core")
        reason = "" if ok else "Python package cspuz_core is not installed"
        return BackendInfo(name, _LABELS[name], ok, reason, False, True)
    if name == "z3":
        ok = _module_available("z3")
        reason = "" if ok else "Python package z3-solver is not installed"
        return BackendInfo(name, _LABELS[name], ok, reason, True, False)
    if name == "csugar":
        ok = _module_available("pycsugar")
        reason = "" if ok else "Python package pycsugar is not installed"
        return BackendInfo(name, _LABELS[name], ok, reason, False, True)

    if os.name == "nt":
        return BackendInfo(
            name,
            _LABELS[name],
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
    return BackendInfo(name, _LABELS[name], ok, reason, timeout_ok, False)


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
        return BackendInfo("auto", _LABELS["auto"], False, str(exc))
    concrete = _concrete_info(resolved)
    primary_infos = [_concrete_info(candidate) for candidate in ("cspuz_core", "z3")]
    timeout_available = any(
        info.available and info.supports_timeout for info in primary_infos
    )
    return BackendInfo(
        "auto",
        _LABELS["auto"],
        True,
        "",
        timeout_available,
        concrete.supports_graph_primitives,
    )


def list_backends() -> tuple[BackendInfo, ...]:
    return tuple(backend_info(name) for name in BACKEND_NAMES)
