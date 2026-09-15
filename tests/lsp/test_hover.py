"""Hover tests for builtins, library defs, imports and puzzle variables."""

from __future__ import annotations

import unittest
from pathlib import Path

from tests.lsp import make_server, open_file, token_pos

ROOT = Path(__file__).resolve().parents[2]


class HoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = make_server()
        cls.shading = ROOT / "puzzle" / "lib" / "shading.dsl"
        cls.nurikabe = ROOT / "impls" / "nurikabe.dsl"
        cls.shading_text = cls.shading.read_text(encoding="utf-8")
        cls.nurikabe_text = cls.nurikabe.read_text(encoding="utf-8")
        cls.shading_uri = open_file(cls.server, cls.shading, cls.shading_text)
        cls.nurikabe_uri = open_file(cls.server, cls.nurikabe, cls.nurikabe_text)

    def _hover(self, uri: str, source: str, name: str, **kwargs) -> str | None:
        line, col = token_pos(source, name, **kwargs)
        result = self.server.hover(
            {"textDocument": {"uri": uri}, "position": {"line": line, "character": col}}
        )
        if result is None:
            return None
        return result["contents"]["value"]

    def test_island_and_wall_rules_are_builtins(self) -> None:
        hitori = ROOT / "impls" / "hitori.dsl"
        hitori_text = hitori.read_text(encoding="utf-8")
        hitori_uri = open_file(self.server, hitori, hitori_text)
        island = self._hover(hitori_uri, hitori_text, "island_rule")
        self.assertIsNotNone(island)
        self.assertIn("(builtin)", island)
        self.assertIn("涂黑格互不相邻", island)
        wall = self._hover(self.nurikabe_uri, self.nurikabe_text, "wall_rule")
        self.assertIsNotNone(wall)
        self.assertIn("(builtin)", wall)
        self.assertIn("涂黑格连通", wall)

    def test_no2x2_library_signature(self) -> None:
        text = self._hover(self.shading_uri, self.shading_text, "no2x2")
        self.assertIsNotNone(text)
        self.assertIn("no2x2", text)
        self.assertIn("core.dsl", text)
        self.assertIn("2x2", text)

    def test_builtin_at(self) -> None:
        source = "at(x, cell(0, 0)) == 0\n"
        uri = open_file(self.server, ROOT / "impls" / "_at_hover.dsl", source)
        text = self._hover(uri, source, "at")
        self.assertIsNotNone(text)
        self.assertIn("(builtin)", text)
        self.assertIn("Category:", text)

    def test_import_shading(self) -> None:
        text = self._hover(self.nurikabe_uri, self.nurikabe_text, "shading")
        self.assertIsNotNone(text)
        self.assertIn("shading.dsl", text)
        self.assertIn("black_connected", text)

    def test_puzzle_variable_x(self) -> None:
        text = self._hover(self.nurikabe_uri, self.nurikabe_text, "x")
        self.assertIsNotNone(text)
        self.assertIn("cell", text)
        self.assertIn("normal", text)
        self.assertIn("[0, 1]", text)

    def test_use_keyword_hover(self) -> None:
        source = "use z3\n"
        uri = open_file(self.server, ROOT / "impls" / "_use_hover.dsl", source)
        line, col = token_pos(source, "use")
        result = self.server.hover(
            {"textDocument": {"uri": uri}, "position": {"line": line, "character": col}}
        )
        self.assertIsNotNone(result)
        self.assertIn("backend", result["contents"]["value"])
        line, col = token_pos(source, "z3")
        result = self.server.hover(
            {"textDocument": {"uri": uri}, "position": {"line": line, "character": col}}
        )
        self.assertIsNotNone(result)
        self.assertIn("features", result["contents"]["value"])

    def test_unknown_returns_null(self) -> None:
        bogus = "zzzz_not_a_name = 1\n"
        # a NAME that does not exist
        uri = open_file(self.server, ROOT / "impls" / "_hover_tmp.dsl", "unknown_ident_xyz\n")
        line, col = token_pos("unknown_ident_xyz\n", "unknown_ident_xyz")
        result = self.server.hover(
            {"textDocument": {"uri": uri}, "position": {"line": line, "character": col}}
        )
        self.assertIsNone(result)
        del bogus


if __name__ == "__main__":
    unittest.main()
