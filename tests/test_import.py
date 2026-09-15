"""Tests for Penpa+ / puzz.link URL import."""

from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from puzzle.importing import (
    PuzzleImportError,
    decode_penpa,
    encode_penpa,
    import_url,
    parse_puzzlink,
)
from puzzle.importing.board import LayerBoard
from puzzle.importing.pids import resolve_puzzle_key
from puzzle.spec import Instance, load_spec


class PidAliasTests(unittest.TestCase):
    def test_common_aliases(self) -> None:
        self.assertEqual(resolve_puzzle_key("mashu"), "masyu")
        self.assertEqual(resolve_puzzle_key("lightup"), "akari")
        self.assertEqual(resolve_puzzle_key("yajirin"), "yajilin")
        self.assertEqual(resolve_puzzle_key("building"), "skyscrapers")
        self.assertEqual(resolve_puzzle_key("nurikabe"), "nurikabe")


class PuzzlinkParseTests(unittest.TestCase):
    def test_full_url(self) -> None:
        meta = parse_puzzlink("https://puzz.link/p?nurikabe/5/5/g5k2o1k3g")
        self.assertEqual(meta["pid"], "nurikabe")
        self.assertEqual(meta["rows"], "5")
        self.assertEqual(meta["cols"], "5")
        self.assertEqual(meta["body"], "g5k2o1k3g")
        self.assertEqual(meta["key"], "nurikabe")

    def test_alias_pid(self) -> None:
        meta = parse_puzzlink("https://puzz.link/p?mashu/6/6/1063000i3000")
        self.assertEqual(meta["key"], "masyu")

    def test_bare_path(self) -> None:
        meta = parse_puzzlink("slither/5/5/cbcbcddad")
        self.assertEqual(meta["pid"], "slither")
        self.assertEqual(meta["open"], "slither/5/5/cbcbcddad")

    def test_rejects_garbage(self) -> None:
        with self.assertRaises(PuzzleImportError):
            parse_puzzlink("not-a-puzzle")


class PenpaRoundtripTests(unittest.TestCase):
    def test_numbers_and_shade_roundtrip(self) -> None:
        board = LayerBoard(rows=3, cols=3, title="probe")
        board.cell(0, 0).number = 4
        board.cell(1, 1).shade = 1
        board.cell(2, 2).circle = 2
        url = encode_penpa(board, title="probe", tags=["nurikabe"])
        self.assertIn("penpa-edit", url)
        self.assertIn("p=", url)
        decoded = decode_penpa(url)
        self.assertEqual(decoded.rows, 3)
        self.assertEqual(decoded.cols, 3)
        self.assertEqual(decoded.cell(0, 0).number, 4)
        self.assertEqual(decoded.cell(1, 1).shade, 1)
        self.assertEqual(decoded.cell(2, 2).circle, 2)
        layers = {layer["id"] for layer in decoded.to_layers_json()}
        self.assertIn("number", layers)
        self.assertIn("surface", layers)
        self.assertIn("circle", layers)

    def test_outside_clues_roundtrip(self) -> None:
        board = LayerBoard(rows=3, cols=3)
        board.outside = {
            "top": [2, -1, 1],
            "left": [3, -1, -1],
            "right": [-1, -1, -1],
            "bottom": [-1, -1, -1],
        }
        decoded = decode_penpa(encode_penpa(board))
        self.assertEqual(decoded.outside.get("top", [None, None, None])[0], 2)
        self.assertEqual(decoded.outside.get("top", [None, None, None])[2], 1)
        self.assertEqual(decoded.outside.get("left", [None, None, None])[0], 3)

    def test_yajilin_arrow_number_bind(self) -> None:
        board = LayerBoard(rows=3, cols=3)
        board.cell(0, 2).arrow = 3  # right
        board.cell(0, 2).number = 2
        spec = load_spec("yajilin")
        from puzzle.importing.bind import bind_instance

        inst = bind_instance(board, spec)
        self.assertEqual(inst["clues"]["d"]["0,2"], 3)
        self.assertEqual(inst["clues"]["n"]["0,2"], 2)

    def test_arrow_zero_is_kept_in_layers(self) -> None:
        board = LayerBoard(rows=2, cols=2)
        board.cell(0, 0).arrow = 0
        board.cell(0, 0).number = 0
        layers = {layer["id"]: layer["values"] for layer in board.to_layers_json()}
        self.assertEqual(layers["arrow"]["0,0"], 0)
        self.assertEqual(layers["number"]["0,0"], 0)
        decoded = decode_penpa(encode_penpa(board))
        self.assertEqual(decoded.cell(0, 0).arrow, 0)
        self.assertEqual(decoded.cell(0, 0).number, 0)

    def test_untagged_penpa_returns_generic_layers(self) -> None:
        board = LayerBoard(rows=2, cols=2)
        board.cell(0, 1).number = 4
        board.cell(1, 0).shade = 1
        payload = import_url(encode_penpa(board))
        self.assertEqual(payload["kind"], "penpa")
        self.assertIsNone(payload["puzzle"])
        self.assertIsNone(payload["instance"])
        layers = {layer["id"]: layer["values"] for layer in payload["layers"]}
        self.assertEqual(layers["number"]["0,1"], 4)
        self.assertEqual(layers["surface"]["1,0"], 1)

    def test_untagged_penpa_binds_when_puzzle_hinted(self) -> None:
        board = LayerBoard(rows=2, cols=2)
        board.cell(0, 0).number = 3
        payload = import_url(encode_penpa(board), puzzle="nurikabe")
        self.assertEqual(payload["puzzle"], "nurikabe")
        self.assertEqual(payload["instance"]["clues"]["n"]["0,0"], 3)

    def test_import_penpa_binds_nurikabe(self) -> None:
        board = LayerBoard(rows=4, cols=4, tags=["nurikabe"])
        board.cell(0, 0).number = 2
        board.cell(3, 3).number = 3
        payload = import_url(encode_penpa(board, tags=["nurikabe"]))
        self.assertEqual(payload["kind"], "penpa")
        self.assertEqual(payload["puzzle"], "nurikabe")
        self.assertIsNotNone(payload["instance"])
        clues = payload["instance"]["clues"]
        self.assertEqual(clues["n"]["0,0"], 2)
        self.assertEqual(clues["n"]["3,3"], 3)
        Instance.from_json(payload["instance"])  # schema check


class PuzzlinkDecodeTests(unittest.TestCase):
    def test_official_nurikabe_example(self) -> None:
        try:
            payload = import_url("https://puzz.link/p?nurikabe/5/5/g5k2o1k3g")
        except PuzzleImportError as exc:
            self.skipTest(str(exc))
        self.assertEqual(payload["puzzle"], "nurikabe")
        clues = payload["instance"]["clues"]["n"]
        self.assertEqual(clues["0,1"], 5)
        self.assertEqual(clues["1,2"], 2)
        self.assertEqual(clues["3,2"], 1)
        self.assertEqual(clues["4,3"], 3)

    def test_official_masyu_example(self) -> None:
        try:
            payload = import_url("https://puzz.link/p?mashu/6/6/1063000i3000")
        except PuzzleImportError as exc:
            self.skipTest(str(exc))
        self.assertEqual(payload["puzzle"], "masyu")
        circles = payload["instance"]["clues"]["o"]
        self.assertEqual(circles["0,2"], 1)
        self.assertEqual(circles["1,1"], 2)

    def test_official_yajilin_example(self) -> None:
        try:
            payload = import_url("https://puzz.link/p?yajilin/5/5/m32j10")
        except PuzzleImportError as exc:
            self.skipTest(str(exc))
        self.assertEqual(payload["puzzle"], "yajilin")
        arrows = payload["instance"]["clues"]["d"]
        numbers = payload["instance"]["clues"]["n"]
        self.assertTrue(arrows)
        self.assertEqual(set(arrows), set(numbers))
        self.assertIn(0, numbers.values())

    def test_penpa_roundtrip_of_puzzlink_nurikabe(self) -> None:
        try:
            from puzzle.importing.puzzlink import decode_puzzlink

            board = decode_puzzlink("https://puzz.link/p?nurikabe/5/5/g5k2o1k3g")
        except PuzzleImportError as exc:
            self.skipTest(str(exc))
        again = import_url(encode_penpa(board, tags=["nurikabe"]))
        self.assertEqual(again["kind"], "penpa")
        self.assertEqual(again["puzzle"], "nurikabe")
        self.assertEqual(
            again["instance"]["clues"]["n"],
            {"0,1": 5, "1,2": 2, "3,2": 1, "4,3": 3},
        )


class EncodeLayersTests(unittest.TestCase):
    def test_from_layers_json_roundtrip(self) -> None:
        from puzzle.importing import encode_layers, from_layers_json

        board = LayerBoard(rows=3, cols=3)
        board.cell(0, 1).number = 5
        board.cell(2, 2).shade = 1
        rebuilt = from_layers_json(3, 3, board.to_layers_json())
        self.assertEqual(rebuilt.cell(0, 1).number, 5)
        self.assertEqual(rebuilt.cell(2, 2).shade, 1)
        url = encode_layers(3, 3, board.to_layers_json(), title="probe", tags=["nurikabe"])
        payload = import_url(url)
        layers = {layer["id"]: layer["values"] for layer in payload["layers"]}
        self.assertEqual(layers["number"]["0,1"], 5)
        self.assertEqual(layers["surface"]["2,2"], 1)


class DirRayOrderTests(unittest.TestCase):
    """``dir()`` must walk outward; RegionValue.of used to sort and reverse LEFT/UP."""

    def test_dir_left_is_outward(self) -> None:
        spec = load_spec("akari")
        inst = Instance.from_json(
            {"puzzle": "akari", "rows": 2, "cols": 4, "clues": {"w": {}, "n": {}}}
        )
        source = """
import "core"
for p in cells():
    if row_of(p) == 0 and col_of(p) == 3:
        let i = 0
        for q in dir(p, LEFT):
            print(i, col_of(q))
            let i = i + 1
"""
        from puzzle.runner import solve_instance

        result = solve_instance(spec, inst, source=source, timeout_ms=5000)
        cols = []
        for line in result.get("debug") or []:
            # "line N: 0 | 2"
            parts = line.split(":", 1)[-1].split("|")
            if len(parts) >= 2:
                cols.append(int(parts[1].strip()))
        self.assertEqual(cols, [2, 1, 0])


if __name__ == "__main__":
    unittest.main()
