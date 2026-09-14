"""Per-backend capability flags used by the DSL compiler.

``use`` / ``backend=`` select a concrete solver. Builtins then either emit a
native operator when the selected backend advertises the feature, or a portable
expansion. Adding a new optional encoding means adding a flag here and gating
the builtin with ``Compiler.require_feature`` or ``features.has``.
"""

from __future__ import annotations

from dataclasses import dataclass

FEATURE_TIMEOUT = "timeout"
FEATURE_GRAPH_VERTEX_CONNECTED = "graph_vertex_connected"
FEATURE_GRAPH_DIVISION = "graph_division"
FEATURE_GRAPH_EDGE_PATH = "graph_edge_path"

FEATURE_DOCS: dict[str, str] = {
    FEATURE_TIMEOUT: "in-process solve timeout",
    FEATURE_GRAPH_VERTEX_CONNECTED: "native active-vertex connectivity",
    FEATURE_GRAPH_DIVISION: "native connected division / borders",
    FEATURE_GRAPH_EDGE_PATH: "native single-path edge constraint (no expansion)",
}


@dataclass(frozen=True)
class BackendFeatures:
    """Optional encodings a concrete solver can actually execute."""

    timeout: bool = False
    graph_vertex_connected: bool = False
    graph_division: bool = False
    graph_edge_path: bool = False

    def has(self, name: str) -> bool:
        return bool(getattr(self, name, False))

    def names(self) -> tuple[str, ...]:
        flags = (
            (FEATURE_TIMEOUT, self.timeout),
            (FEATURE_GRAPH_VERTEX_CONNECTED, self.graph_vertex_connected),
            (FEATURE_GRAPH_DIVISION, self.graph_division),
            (FEATURE_GRAPH_EDGE_PATH, self.graph_edge_path),
        )
        return tuple(name for name, enabled in flags if enabled)


# Conservative catalogue: only enable a native operator when the pinned cspuz
# backend is known to implement it. Sugar may support graph ops depending on
# the executable, but this project does not probe that, so it stays off.
FEATURES_BY_BACKEND: dict[str, BackendFeatures] = {
    "cspuz_core": BackendFeatures(
        graph_vertex_connected=True,
        graph_division=True,
        graph_edge_path=True,
    ),
    "z3": BackendFeatures(timeout=True),
    "csugar": BackendFeatures(
        graph_vertex_connected=True,
        graph_edge_path=True,
    ),
    "sugar": BackendFeatures(),
    "sugar_extended": BackendFeatures(),
}

DEFAULT_FEATURES = BackendFeatures()

_BACKEND_ORDER = ("cspuz_core", "z3", "csugar", "sugar", "sugar_extended")


def features_for(backend: str) -> BackendFeatures:
    """Return the feature set of a *concrete* backend name (not ``auto``)."""

    return FEATURES_BY_BACKEND.get(backend, DEFAULT_FEATURES)


def backends_with_feature(feature: str) -> tuple[str, ...]:
    """Concrete backend names that advertise ``feature``, in catalogue order."""

    return tuple(name for name in _BACKEND_ORDER if features_for(name).has(feature))
