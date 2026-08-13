"""JSON-RPC 2.0 over LSP stdio frames (``Content-Length`` + JSON body).

Stdlib only: no ``pygls``. Callers pass binary streams (``sys.stdin.buffer``).
"""

from __future__ import annotations

import json
import sys
import threading
from typing import Any, Callable, TextIO


PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

MAX_HEADER = 64 * 1024
MAX_BODY = 32 * 1024 * 1024


class RpcError(Exception):
    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

    def to_payload(self) -> dict:
        error: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            error["data"] = self.data
        return error


class MessageReader:
    """Buffered LSP frame reader that copes with split TCP/pipe reads."""

    def __init__(self, stream, max_header: int = MAX_HEADER, max_body: int = MAX_BODY) -> None:
        self.stream = stream
        self.max_header = max_header
        self.max_body = max_body
        self._buf = b""

    def _pull(self, size: int = 4096) -> bool:
        # ``BufferedReader.read(n)`` waits until *n* bytes or EOF. VS Code (and
        # our tests) keep stdin open, so on Windows that blocks forever after a
        # short frame. ``read1`` issues a single raw read and returns whatever
        # is available; ``BytesIO`` has no ``read1`` and ``read`` is fine.
        read1 = getattr(self.stream, "read1", None)
        chunk = read1(size) if read1 is not None else self.stream.read(size)
        if not chunk:
            return False
        self._buf += chunk
        return True

    def read(self) -> dict | None:
        """Read one JSON-RPC message. ``None`` means the stream closed."""

        while b"\r\n\r\n" not in self._buf:
            if len(self._buf) > self.max_header:
                raise ValueError("LSP header too large")
            if not self._pull():
                return None
        raw_headers, self._buf = self._buf.split(b"\r\n\r\n", 1)
        if len(raw_headers) > self.max_header:
            raise ValueError("LSP header too large")
        length: int | None = None
        for line in raw_headers.split(b"\r\n"):
            if b":" not in line:
                continue
            key, value = line.split(b":", 1)
            if key.strip().lower() == b"content-length":
                try:
                    length = int(value.strip())
                except ValueError as exc:
                    raise ValueError("invalid Content-Length") from exc
        if length is None:
            raise ValueError("missing Content-Length")
        if length < 0 or length > self.max_body:
            raise ValueError("LSP body length out of range")
        while len(self._buf) < length:
            if not self._pull(max(4096, length - len(self._buf))):
                raise ValueError("unexpected EOF in LSP body")
        body, self._buf = self._buf[:length], self._buf[length:]
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RpcError(PARSE_ERROR, f"invalid JSON: {exc}") from exc


def write_message(stream, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    stream.write(header + body)
    stream.flush()


Handler = Callable[[str, Any], Any]


class Rpc:
    """Read loop: dispatch requests, reply, and send notifications out."""

    def __init__(self, reader, writer, log: TextIO | None = None) -> None:
        self.reader = MessageReader(reader)
        self.writer = writer
        self.log = log or sys.stderr
        self._write_lock = threading.Lock()
        self._alive = True

    def _emit(self, payload: dict) -> None:
        with self._write_lock:
            write_message(self.writer, payload)

    def notify(self, method: str, params: Any = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._emit(payload)

    def reply(self, msg_id: Any, result: Any) -> None:
        self._emit({"jsonrpc": "2.0", "id": msg_id, "result": result})

    def reply_error(self, msg_id: Any, error: RpcError) -> None:
        self._emit({"jsonrpc": "2.0", "id": msg_id, "error": error.to_payload()})

    def listen(self, handler: Handler) -> None:
        while self._alive:
            try:
                message = self.reader.read()
            except RpcError as exc:
                self._emit({"jsonrpc": "2.0", "id": None, "error": exc.to_payload()})
                continue
            except ValueError as exc:
                self._trace(f"frame error: {exc}")
                self._emit({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": RpcError(PARSE_ERROR, str(exc)).to_payload(),
                })
                continue
            if message is None:
                break
            self._dispatch(message, handler)

    def stop(self) -> None:
        self._alive = False

    def _dispatch(self, message: dict, handler: Handler) -> None:
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            self._emit({
                "jsonrpc": "2.0",
                "id": message.get("id") if isinstance(message, dict) else None,
                "error": RpcError(INVALID_REQUEST, "invalid JSON-RPC message").to_payload(),
            })
            return
        method = message.get("method")
        msg_id = message.get("id", _MISSING)
        params = message.get("params")
        is_request = msg_id is not _MISSING
        if not method:
            if is_request:
                self.reply_error(msg_id, RpcError(INVALID_REQUEST, "missing method"))
            return
        try:
            result = handler(method, params)
        except RpcError as exc:
            if is_request:
                self.reply_error(msg_id, exc)
            else:
                self._trace(f"{method}: {exc.message}")
            return
        except Exception as exc:  # noqa: BLE001 — never crash the server loop
            self._trace(f"{method} crashed: {exc}")
            if is_request:
                self.reply_error(msg_id, RpcError(INTERNAL_ERROR, str(exc)))
            return
        if is_request:
            self.reply(msg_id, result)

    def _trace(self, text: str) -> None:
        try:
            self.log.write(text + "\n")
            self.log.flush()
        except Exception:
            pass


_MISSING = object()
