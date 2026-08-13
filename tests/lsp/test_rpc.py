"""Frame parser tests for the stdlib JSON-RPC transport."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import threading
import unittest
from pathlib import Path

from puzzle.lsp.convert import path_to_uri
from puzzle.lsp.rpc import MessageReader, write_message

ROOT = Path(__file__).resolve().parents[2]


class _OneByte(io.BytesIO):
    """Force 1-byte reads to simulate split packets."""

    def read(self, size: int = -1) -> bytes:  # noqa: A003
        if size is None or size < 0:
            return super().read(size)
        return super().read(1)


class RpcFrameTests(unittest.TestCase):
    def test_roundtrip(self) -> None:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"x": 1}}
        buf = io.BytesIO()
        write_message(buf, payload)
        buf.seek(0)
        got = MessageReader(buf).read()
        self.assertEqual(got, payload)

    def test_split_reads(self) -> None:
        payload = {"jsonrpc": "2.0", "method": "textDocument/didOpen", "params": {"n": 99}}
        raw = io.BytesIO()
        write_message(raw, payload)
        split = _OneByte(raw.getvalue())
        got = MessageReader(split).read()
        self.assertEqual(got, payload)

    def test_utf8_multibyte_body(self) -> None:
        payload = {"jsonrpc": "2.0", "id": 2, "result": {"text": "中文文档 😀"}}
        buf = io.BytesIO()
        write_message(buf, payload)
        buf.seek(0)
        got = MessageReader(buf).read()
        self.assertEqual(got["result"]["text"], "中文文档 😀")

    def test_content_type_header_ignored(self) -> None:
        body = json.dumps({"jsonrpc": "2.0", "id": 3, "method": "shutdown"}).encode("utf-8")
        frame = (
            b"Content-Length: %d\r\nContent-Type: application/vscode-jsonrpc; charset=utf-8\r\n\r\n"
            % len(body)
        ) + body
        got = MessageReader(io.BytesIO(frame)).read()
        self.assertEqual(got["method"], "shutdown")

    def test_oversize_header(self) -> None:
        junk = b"X-Foo: " + (b"a" * 70_000) + b"\r\n\r\n{}"
        with self.assertRaises(ValueError):
            MessageReader(io.BytesIO(junk), max_header=1024).read()

    def test_read1_used_for_short_frames(self) -> None:
        """Buffered pipes must not ``read(n)``-wait for n bytes (Windows hang)."""

        payload = {"jsonrpc": "2.0", "id": 7, "method": "ping"}
        raw = io.BytesIO()
        write_message(raw, payload)
        data = raw.getvalue()

        class _NeedRead1:
            def __init__(self, blob: bytes) -> None:
                self._blob = blob

            def read(self, size: int = -1) -> bytes:
                raise AssertionError("read() would block on an open Windows pipe")

            def read1(self, size: int = -1) -> bytes:
                n = 16 if size is None or size < 0 else size
                chunk, self._blob = self._blob[:n], self._blob[n:]
                return chunk

        got = MessageReader(_NeedRead1(data)).read()
        self.assertEqual(got, payload)

    def test_two_messages_in_one_buffer(self) -> None:
        buf = io.BytesIO()
        write_message(buf, {"jsonrpc": "2.0", "id": 1, "method": "a"})
        write_message(buf, {"jsonrpc": "2.0", "id": 2, "method": "b"})
        buf.seek(0)
        reader = MessageReader(buf)
        self.assertEqual(reader.read()["id"], 1)
        self.assertEqual(reader.read()["id"], 2)


class ConvertTests(unittest.TestCase):
    def test_utf32_is_identity(self) -> None:
        from puzzle.lsp.convert import codepoint_to_lsp, lsp_to_codepoint, negotiate_encoding

        self.assertEqual(negotiate_encoding(["utf-16", "utf-32"]), "utf-32")
        line = "abc中文"
        self.assertEqual(codepoint_to_lsp(line, 4, "utf-32"), 4)
        self.assertEqual(lsp_to_codepoint(line, 4, "utf-32"), 4)

    def test_utf16_emoji(self) -> None:
        from puzzle.lsp.convert import codepoint_to_lsp, lsp_to_codepoint

        line = "a😀b"  # 😀 is one code point, two UTF-16 units
        self.assertEqual(codepoint_to_lsp(line, 2, "utf-16"), 3)
        self.assertEqual(lsp_to_codepoint(line, 3, "utf-16"), 2)

    def test_one_based_position(self) -> None:
        from puzzle.lsp.convert import position, position_from_lsp

        source = "def foo():\n    pass\n"
        pos = position(1, 5, source, "utf-32")
        self.assertEqual(pos, {"line": 0, "character": 4})
        self.assertEqual(position_from_lsp(pos, source, "utf-32"), (1, 5))


class E2EProcessTests(unittest.TestCase):
    def test_initialize_hover_definition_shutdown(self) -> None:
        import os

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        proc = subprocess.Popen(
            [sys.executable, "-u", "-m", "puzzle.lsp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=str(ROOT),
            bufsize=0,
            env=env,
        )
        assert proc.stdin is not None and proc.stdout is not None
        reader = MessageReader(proc.stdout)
        msg_id = 0
        watchdog = threading.Timer(20.0, proc.kill)
        watchdog.daemon = True
        watchdog.start()

        def request(method: str, params):
            nonlocal msg_id
            msg_id += 1
            write_message(
                proc.stdin,
                {"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params},
            )
            proc.stdin.flush()
            while True:
                message = reader.read()
                self.assertIsNotNone(message)
                if message.get("id") == msg_id:
                    return message

        def notify(method: str, params) -> None:
            write_message(proc.stdin, {"jsonrpc": "2.0", "method": method, "params": params})
            proc.stdin.flush()

        try:
            init = request(
                "initialize",
                {
                    "processId": None,
                    "rootUri": path_to_uri(ROOT),
                    "capabilities": {"general": {"positionEncodings": ["utf-32"]}},
                    "initializationOptions": {"diagnosticsLevel": "syntax"},
                },
            )
            self.assertIn("capabilities", init["result"])
            notify("initialized", {})
            shading = ROOT / "puzzle" / "lib" / "shading.dsl"
            text = shading.read_text(encoding="utf-8")
            uri = path_to_uri(shading)
            notify(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "puzzle-dsl",
                        "version": 1,
                        "text": text,
                    }
                },
            )
            from tests.lsp import token_pos

            line, col = token_pos(text, "island_rule", after_def=True)
            hover = request(
                "textDocument/hover",
                {"textDocument": {"uri": uri}, "position": {"line": line, "character": col}},
            )
            self.assertIsNotNone(hover.get("result"))
            self.assertIn("涂黑格互不相邻", hover["result"]["contents"]["value"])
            nurikabe = ROOT / "impls" / "nurikabe.dsl"
            ntext = nurikabe.read_text(encoding="utf-8")
            nuri = path_to_uri(nurikabe)
            notify(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": nuri,
                        "languageId": "puzzle-dsl",
                        "version": 1,
                        "text": ntext,
                    }
                },
            )
            wline, wcol = token_pos(ntext, "wall_rule")
            definition = request(
                "textDocument/definition",
                {
                    "textDocument": {"uri": nuri},
                    "position": {"line": wline, "character": wcol},
                },
            )
            loc = definition["result"]
            self.assertIsNotNone(loc)
            self.assertTrue(str(loc["uri"]).endswith("shading.dsl") or "shading.dsl" in loc["uri"])
            request("shutdown", None)
            notify("exit", None)
        finally:
            watchdog.cancel()
            try:
                proc.stdin.close()
            except Exception:
                pass
            try:
                proc.stdout.close()
            except Exception:
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
        self.assertEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
