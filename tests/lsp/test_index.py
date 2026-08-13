"""Symbol index tests against the real ``.dsl`` corpus."""

from __future__ import annotations

import unittest
from pathlib import Path

from puzzle.dsl.parser import parse
from puzzle.lsp.convert import path_to_uri
from puzzle.lsp.index import Index, iter_defs

ROOT = Path(__file__).resolve().parents[2]


class IndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = Index(ROOT)
        cls.index.build()

    def test_indexes_all_dsl_files(self) -> None:
        lib = list((ROOT / "puzzle" / "lib").glob("*.dsl"))
        impls = list((ROOT / "impls").glob("*.dsl"))
        expected = {path_to_uri(p.resolve()) for p in lib + impls}
        self.assertTrue(expected)
        missing = expected - set(self.index.files)
        self.assertEqual(missing, set(), f"index missed {len(missing)} file(s)")

    def test_shading_defs_have_correct_lines(self) -> None:
        path = ROOT / "puzzle" / "lib" / "shading.dsl"
        source = path.read_text(encoding="utf-8")
        program = parse(source)
        expected = {}
        for stmt, nested in iter_defs(program.statements):
            if nested:
                continue
            expected[stmt.name] = stmt.name_line or stmt.line
        entry = self.index.files[path_to_uri(path.resolve())]
        got = {sym.name: sym.line for sym in entry.symbols if not sym.nested}
        self.assertEqual(got, expected)
        self.assertIn("island_rule", got)
        self.assertIn("wall_rule", got)
        self.assertEqual(got["island_rule"], 42)
        self.assertEqual(got["wall_rule"], 47)

    def test_parse_failure_keeps_previous(self) -> None:
        path = ROOT / "puzzle" / "lib" / "core.dsl"
        uri = path_to_uri(path.resolve())
        before = list(self.index.files[uri].symbols)
        self.assertTrue(before)
        self.index.index_path(path, text="def broken(\n")
        after = self.index.files[uri]
        self.assertFalse(after.ok)
        self.assertEqual([s.name for s in after.symbols], [s.name for s in before])
        # restore
        self.index.index_path(path)

    def test_visible_functions_follow_imports(self) -> None:
        nurikabe = path_to_uri((ROOT / "impls" / "nurikabe.dsl").resolve())
        visible = self.index.visible_functions(nurikabe)
        self.assertIn("wall_rule", visible)
        self.assertTrue(visible["wall_rule"].uri.endswith("shading.dsl") or "shading.dsl" in visible["wall_rule"].uri)
        self.assertIn("no2x2", visible)
        self.assertIn("island_rule", visible)


if __name__ == "__main__":
    unittest.main()
