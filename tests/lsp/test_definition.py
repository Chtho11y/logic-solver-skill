"""Go-to-definition tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from tests.lsp import make_server, open_file, token_pos

ROOT = Path(__file__).resolve().parents[2]


class DefinitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = make_server()
        cls.nurikabe = ROOT / "impls" / "nurikabe.dsl"
        cls.shading = ROOT / "puzzle" / "lib" / "shading.dsl"
        cls.ntext = cls.nurikabe.read_text(encoding="utf-8")
        cls.stext = cls.shading.read_text(encoding="utf-8")
        cls.nuri = open_file(cls.server, cls.nurikabe, cls.ntext)
        cls.suri = open_file(cls.server, cls.shading, cls.stext)

    def _def(self, uri: str, source: str, name: str, **kwargs):
        line, col = token_pos(source, name, **kwargs)
        return self.server.definition(
            {"textDocument": {"uri": uri}, "position": {"line": line, "character": col}}
        )

    def test_wall_rule_jumps_to_shading(self) -> None:
        loc = self._def(self.nuri, self.ntext, "wall_rule")
        self.assertIsNotNone(loc)
        self.assertIn("shading.dsl", loc["uri"])
        self.assertEqual(loc["range"]["start"]["line"], 46)  # 0-based; def is line 47

    def test_import_jumps_to_library_file(self) -> None:
        loc = self._def(self.nuri, self.ntext, "shading")
        self.assertIsNotNone(loc)
        self.assertIn("shading.dsl", loc["uri"])
        self.assertEqual(loc["range"]["start"]["line"], 0)

    def test_builtin_does_not_jump(self) -> None:
        loc = self._def(self.suri, self.stext, "at")
        self.assertIsNone(loc)

    def test_document_symbols_list_defs(self) -> None:
        symbols = self.server.document_symbol({"textDocument": {"uri": self.suri}})
        names = [item["name"].split("(")[0] for item in symbols]
        self.assertIn("island_rule", names)
        self.assertIn("wall_rule", names)

    def test_workspace_symbol(self) -> None:
        hits = self.server.workspace_symbol({"query": "island_rule"})
        self.assertTrue(any("island_rule" in item["name"] for item in hits))


if __name__ == "__main__":
    unittest.main()
