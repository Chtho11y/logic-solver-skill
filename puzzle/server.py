"""A dependency-free HTTP API in front of the puzzle solver.

    python -m puzzle.server --port 8000

Endpoints (all JSON):

======================  ======  ===========================================
``/api/health``         GET     solver availability and backend catalogue
``/api/rules``          GET     every rule from ``rules.txt``
``/api/rules/search``   GET     ``?q=`` name or rule-text lookup
``/api/elements``       GET     the generic drawing-element catalogue
``/api/puzzles``        GET     implemented puzzle specs (with layers)
``/api/puzzles/<key>``  GET     one spec, its DSL source and sample instance
``/api/solve``          POST    ``{"instance": {...}}`` -> solved values
======================  ======  ===========================================

Static files from ``web/dist`` (the built front-end) are served at ``/`` when
present, so a production build is reachable from the same origin.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from puzzle.backends import BackendError, backend_info, resolve_backend  # noqa: E402
from puzzle.dsl import backend_status, function_table, is_available  # noqa: E402
from puzzle.elements import elements_json  # noqa: E402
from puzzle.registry import catalogue, get_rule, search_by_description, search_rules  # noqa: E402
from puzzle.runner import DEFAULT_TIMEOUT_MS, solve_payload  # noqa: E402
from puzzle.spec import implemented_keys, load_sample, load_spec  # noqa: E402

WEB_DIST = ROOT / "web" / "dist"
MAX_BODY = 4 * 1024 * 1024


def _default_backend() -> str:
    auto = backend_info("auto")
    timeout = DEFAULT_TIMEOUT_MS if auto.supports_timeout else None
    return resolve_backend("auto", timeout_ms=timeout)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(WEB_DIST), **kwargs)

    def log_message(self, fmt: str, *args) -> None:  # quieter console
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # -- helpers --------------------------------------------------------

    def _send_json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            raise ValueError("missing or oversized request body")
        return json.loads(self.rfile.read(length).decode("utf-8"))

    # -- routing --------------------------------------------------------

    def do_OPTIONS(self) -> None:  # noqa: N802 - http.server API
        self._send_json({"ok": True})

    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        if not url.path.startswith("/api/"):
            if WEB_DIST.is_dir():
                return super().do_GET()
            return self._send_json(
                {"error": "front-end not built; run `npm run build` in web/"}, 404
            )
        try:
            self._route_get(url.path, parse_qs(url.query))
        except FileNotFoundError as exc:
            self._send_json({"error": str(exc)}, 404)
        except Exception as exc:
            traceback.print_exc()
            self._send_json({"error": str(exc)}, 500)

    def _route_get(self, path: str, query: dict) -> None:
        if path == "/api/health":
            backends = backend_status()
            try:
                default_backend = _default_backend()
            except BackendError:
                default_backend = ""
            z3 = next((b["available"] for b in backends if b["name"] == "z3"), False)
            return self._send_json(
                {
                    "ok": True,
                    "solver": {
                        "available": is_available(),
                        "default": default_backend,
                        "backends": backends,
                    },
                    # Transitional field for older web clients.
                    "z3": z3,
                }
            )
        if path == "/api/rules":
            return self._send_json({"rules": catalogue()})
        if path == "/api/rules/search":
            q = (query.get("q") or [""])[0]
            limit = int((query.get("limit") or ["10"])[0])
            by_name = [
                entry.to_json() | {"score": round(score, 2)}
                for entry, score in search_rules(q, limit)
            ]
            by_text = [
                entry.to_json() | {"score": round(score, 2)}
                for entry, score in search_by_description(q, limit)
            ]
            return self._send_json({"query": q, "byName": by_name, "byRule": by_text})
        if path == "/api/elements":
            return self._send_json({"elements": elements_json()})
        if path == "/api/builtins":
            return self._send_json(
                {"entries": [entry.__dict__ for entry in function_table()]}
            )
        if path == "/api/puzzles":
            return self._send_json(
                {"puzzles": [load_spec(key).to_json() for key in implemented_keys()]}
            )
        if path.startswith("/api/puzzles/"):
            key = path[len("/api/puzzles/"):].strip("/")
            spec = load_spec(key)
            instance = load_sample(key)
            rule = get_rule(key)
            return self._send_json(
                {
                    "puzzle": spec.to_json(include_source=True),
                    "sample": instance.to_json() if instance else None,
                    "rule": rule.to_json() if rule else None,
                }
            )
        self._send_json({"error": f"unknown endpoint {path}"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        if url.path != "/api/solve":
            return self._send_json({"error": f"unknown endpoint {url.path}"}, 404)
        try:
            payload = self._read_json()
        except Exception as exc:
            return self._send_json({"status": "error", "message": str(exc)}, 400)
        try:
            self._send_json(solve_payload(payload))
        except FileNotFoundError as exc:
            self._send_json({"status": "error", "message": str(exc)}, 404)
        except Exception as exc:
            traceback.print_exc()
            self._send_json({"status": "error", "message": str(exc)}, 500)


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = HTTPServer((host, port), Handler)
    try:
        default_backend = _default_backend()
    except BackendError:
        default_backend = "unavailable"
    print(
        f"puzzle server on http://{host}:{port}  "
        f"(solver: {default_backend}, available: {is_available()})"
    )
    if not WEB_DIST.is_dir():
        print("note: web/dist not found — run the Vite dev server for the UI")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="puzzle solver HTTP API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    serve(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
