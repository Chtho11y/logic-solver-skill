"""Semantic-token and diagnostic tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from puzzle.lsp.server import TOKEN_MODIFIERS, TOKEN_TYPES
from tests.lsp import make_server, open_file, token_pos

ROOT = Path(__file__).resolve().parents[2]


def decode(data: list[int]) -> list[tuple[int, int, int, str, int]]:
    line = 0
    start = 0
    out = []
    for index in range(0, len(data), 5):
        dline, dstart, length, typ, mods = data[index : index + 5]
        line += dline
        start = dstart if dline else start + dstart
        out.append((line, start, length, TOKEN_TYPES[typ], mods))
    return out


def mod_mask(*names: str) -> int:
    bits = 0
    for name in names:
        bits |= 1 << TOKEN_MODIFIERS.index(name)
    return bits


class SemanticTokenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = make_server()
        cls.shading = ROOT / "puzzle" / "lib" / "shading.dsl"
        cls.text = cls.shading.read_text(encoding="utf-8")
        cls.uri = open_file(cls.server, cls.shading, cls.text)
        result = cls.server.semantic_tokens({"textDocument": {"uri": cls.uri}})
        cls.tokens = decode(result["data"])

    def _at(self, name: str, **kwargs):
        line, col = token_pos(self.text, name, **kwargs)
        matches = [t for t in self.tokens if t[0] == line and t[1] == col]
        self.assertTrue(matches, f"no semantic token for {name!r} at {line}:{col}")
        return matches[0]

    def test_def_keyword(self) -> None:
        tok = self._at("def")
        self.assertEqual(tok[3], "keyword")

    def test_function_declaration(self) -> None:
        tok = self._at("island_rule", after_def=True)
        self.assertEqual(tok[3], "function")
        self.assertEqual(tok[4], mod_mask("declaration"))

    def test_builtin_call(self) -> None:
        tok = self._at("at")
        self.assertEqual(tok[3], "function")
        self.assertEqual(tok[4], mod_mask("defaultLibrary"))

    def test_library_call(self) -> None:
        tok = self._at("no2x2")
        self.assertEqual(tok[3], "function")
        self.assertEqual(tok[4], 0)

    def test_number_and_string(self) -> None:
        numbers = [t for t in self.tokens if t[3] == "number"]
        strings = [t for t in self.tokens if t[3] == "string"]
        self.assertTrue(numbers)
        self.assertTrue(strings)

    def test_lex_error_returns_empty(self) -> None:
        uri = open_file(self.server, ROOT / "impls" / "_bad.dsl", "@@@\n")
        result = self.server.semantic_tokens({"textDocument": {"uri": uri}})
        self.assertEqual(result["data"], [])


class DiagnosticTests(unittest.TestCase):
    def test_syntax_error_range(self) -> None:
        server = make_server()
        nurikabe = ROOT / "impls" / "nurikabe.dsl"
        text = nurikabe.read_text(encoding="utf-8").replace("wall_rule(x)", "wall_rule(x")
        uri = open_file(server, nurikabe, text)
        diags = [item for item in server.published if item["uri"] == uri][-1]["diagnostics"]
        self.assertTrue(diags)
        self.assertEqual(diags[0]["severity"], 1)
        self.assertGreaterEqual(diags[0]["range"]["start"]["line"], 0)

    def test_corpus_has_no_t1_diagnostics(self) -> None:
        server = make_server()
        files = list((ROOT / "puzzle" / "lib").glob("*.dsl")) + list((ROOT / "impls").glob("*.dsl"))
        self.assertGreaterEqual(len(files), 50)
        failures = []
        for path in files:
            uri = open_file(server, path)
            payload = [item for item in server.published if item["uri"] == uri][-1]
            if payload["diagnostics"]:
                failures.append((path.name, payload["diagnostics"][0]["message"]))
        self.assertEqual(failures, [], f"T1 diagnostics on corpus: {failures[:5]}")

    def test_t2_unknown_name(self) -> None:
        from puzzle.dsl.solver import is_available

        if not is_available():
            self.skipTest("z3 is not installed")
        server = make_server()
        path = ROOT / "impls" / "nurikabe.dsl"
        text = path.read_text(encoding="utf-8").replace("wall_rule", "wall_rule_renamed")
        uri = open_file(server, path, text)
        # T2 runs on open (include_semantic=True)
        diags = [item for item in server.published if item["uri"] == uri][-1]["diagnostics"]
        messages = " ".join(d["message"] for d in diags)
        self.assertIn("unknown name", messages.lower())


if __name__ == "__main__":
    unittest.main()
