"""URL and dependency failures must not silently change an imported puzzle."""

from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from unittest.mock import patch

from puzzle.importing import PuzzleImportError, import_url
from puzzle.importing.puzzlink import (
    DUMP_JS,
    _run_pzpr_dump,
    decode_puzzlink,
    layerboard_from_pzpr,
    looks_like_puzzlink,
    parse_puzzlink,
)


class PuzzlinkRobustParseTests(unittest.TestCase):
    def test_flags_survive_full_bare_and_mirror_links(self) -> None:
        payload = "yajilin/b/5/3/m32j10"
        for url in (
            payload,
            "?" + payload,
            "p?" + payload,
            "https://puzz.link/p?" + payload,
            "https://pzv.jp/p.html?" + payload,
            "https://pzprxs.vercel.app/p?" + payload,
            "pzplus.tck.mn/p?" + payload,
            "//puzz.link/p?" + payload,
            "https://mirror.example/puzzle.html?" + payload,
        ):
            with self.subTest(url=url):
                self.assertTrue(looks_like_puzzlink(url))
                meta = parse_puzzlink(url)
                self.assertEqual(meta["open"], payload)
                self.assertEqual(meta["flags"], "b")
                self.assertEqual((meta["rows"], meta["cols"]), ("3", "5"))
                self.assertEqual(meta["body"], "m32j10")

    def test_explicit_empty_flag_and_empty_body(self) -> None:
        meta = parse_puzzlink("slither//2/3/")
        self.assertEqual(meta["open"], "slither//2/3/")
        self.assertEqual(meta["flags"], "")
        self.assertEqual(meta["body"], "")
        self.assertEqual(parse_puzzlink("slither/2/3")["body"], "")

    def test_url_decoding_preserves_plus_and_body_segments(self) -> None:
        meta = parse_puzzlink("https://puzz.link/p?nurikabe%2F3%2F2%2F+123%2B/abc&view=1#note")
        self.assertEqual(meta["open"], "nurikabe/3/2/+123+/abc")
        self.assertEqual(meta["body"], "+123+/abc")

    def test_bare_fragment_is_not_puzzle_data(self) -> None:
        self.assertEqual(parse_puzzlink("nurikabe/3/2/123#note")["body"], "123")

    def test_rejects_invalid_sizes_encodings_and_missing_payload(self) -> None:
        for url in (
            "", "not-a-puzzle", "slither/0/3/1", "slither/3/0/1",
            "slither/-1/3/1", "slither/3/2.5/1", "slither/b/3",
            "slither/3/２/1", "slither/3/2/%zz", "slither/3/2/%ff",
            "https://puzz.link/p", "https://[bad/p?slither/3/3/1",
            "file://puzz.link/p?slither/3/3/1", "slither/3/2/a%0Ab",
            "slither/3/2/a\nb", "slither/3/2/a\tb",
        ):
            with self.subTest(url=url), self.assertRaises(PuzzleImportError):
                parse_puzzlink(url)

    def test_detector_does_not_use_hostname_substrings(self) -> None:
        self.assertFalse(looks_like_puzzlink("notpuzz.link.example/no-puzzle"))
        self.assertFalse(looks_like_puzzlink("notes about puzz.link"))
        self.assertTrue(looks_like_puzzlink("https://puzz.link/p?broken"))


class PuzzlinkDecoderFailureTests(unittest.TestCase):
    def test_missing_node_has_setup_instructions(self) -> None:
        with patch("puzzle.importing.puzzlink.shutil.which", return_value=None):
            with self.assertRaisesRegex(PuzzleImportError, "install Node.js"):
                _run_pzpr_dump("nurikabe/2/2/1")

    def test_decoder_never_starts_npm_and_keeps_useful_error(self) -> None:
        result = subprocess.CompletedProcess([], 1, "", "missing pzpr; run npm install\n    at main (helper.js:1)\n")
        with patch("puzzle.importing.puzzlink.shutil.which", return_value="/bin/node"), \
                patch("puzzle.importing.puzzlink.subprocess.run", return_value=result) as run:
            with self.assertRaisesRegex(PuzzleImportError, "^missing pzpr; run npm install$"):
                _run_pzpr_dump("nurikabe/2/2/1")
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], ["/bin/node", str(DUMP_JS), "nurikabe/2/2/1"])

    def test_subprocess_failures_are_import_errors(self) -> None:
        for error in (OSError("permission denied"), subprocess.TimeoutExpired("node", 20)):
            with self.subTest(error=error), \
                    patch("puzzle.importing.puzzlink.shutil.which", return_value="/bin/node"), \
                    patch("puzzle.importing.puzzlink.subprocess.run", side_effect=error), \
                    self.assertRaises(PuzzleImportError):
                _run_pzpr_dump("nurikabe/2/2/1")

    def test_non_json_and_non_object_dumps_are_import_errors(self) -> None:
        for output in ("not json", "[]", "null"):
            result = subprocess.CompletedProcess([], 0, output, "")
            with self.subTest(output=output), \
                    patch("puzzle.importing.puzzlink.shutil.which", return_value="/bin/node"), \
                    patch("puzzle.importing.puzzlink.subprocess.run", return_value=result), \
                    self.assertRaises(PuzzleImportError):
                _run_pzpr_dump("nurikabe/2/2/1")

    def test_bad_dump_dimensions_are_import_errors(self) -> None:
        for dumped in ({}, {"rows": None, "cols": 2}, {"rows": 0, "cols": 2}):
            with self.subTest(dumped=dumped), self.assertRaises(PuzzleImportError):
                layerboard_from_pzpr(dumped)

    def test_decoder_cannot_silently_change_dimensions(self) -> None:
        with patch("puzzle.importing.puzzlink._run_pzpr_dump", return_value={"rows": 3, "cols": 3}):
            with self.assertRaisesRegex(PuzzleImportError, "changed the puzzle dimensions"):
                decode_puzzlink("nurikabe/2/2/1")


class PuzzlinkClueSemanticsTests(unittest.TestCase):
    def test_unknown_number_is_not_a_shaded_cell(self) -> None:
        board = layerboard_from_pzpr({
            "pid": "nurikabe", "rows": 2, "cols": 2,
            "cells": [{"r": 0, "c": 0, "qnum": -2}],
        })
        self.assertIsNone(board.cell(0, 0).shade)
        self.assertEqual(board.cell(0, 0).number_text, "?")
        self.assertTrue(any("unknown number" in warning for warning in board.warnings))

    def test_akari_unknown_number_still_means_unnumbered_wall(self) -> None:
        board = layerboard_from_pzpr({
            "pid": "lightup", "rows": 2, "cols": 2,
            "cells": [{"r": 0, "c": 0, "qnum": -2}],
        })
        self.assertEqual(board.cell(0, 0).shade, 1)
        self.assertEqual(board.cell(0, 0).number_text, "")

    def test_shakashaka_unnumbered_black_clue_is_not_unknown_number(self) -> None:
        board = layerboard_from_pzpr({
            "pid": "shakashaka", "rows": 2, "cols": 2,
            "cells": [{"r": 0, "c": 0, "qnum": -2}],
        })
        self.assertEqual(board.cell(0, 0).shade, 1)
        self.assertEqual(board.cell(0, 0).number_text, "")

    def test_single_room_requires_positive_given_room_metadata(self) -> None:
        for has_rooms in (False, True):
            board = layerboard_from_pzpr({"rows": 2, "cols": 2, "hasGivenRooms": has_rooms})
            self.assertEqual(len(board.regions), 4 if has_rooms else 0)


class PuzzlinkNodeDependencyTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_missing_pzpr_has_actionable_error_without_installing(self) -> None:
        # Make only pzpr resolution fail, without changing installed packages.
        script = """
const Module = require('module');
const resolve = Module._resolveFilename;
Module._resolveFilename = function(name, ...args) {
  if (name === 'pzpr') throw new Error('Cannot find module pzpr');
  return resolve.call(this, name, ...args);
};
const helper = process.argv[1];
process.argv = [process.execPath, helper, 'nurikabe/2/2/1'];
require(helper);
"""
        proc = subprocess.run([shutil.which("node"), "-e", script, str(DUMP_JS)], capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        self.assertIn("npm --prefix puzzle/importing install", proc.stderr)
        self.assertNotIn("at main", proc.stderr)


class PuzzlinkInstalledIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        node = shutil.which("node")
        if not node:
            raise unittest.SkipTest("Node.js is not installed")
        script = "require.resolve('pzpr', {paths: [" + json.dumps(str(DUMP_JS.parent)) + ", process.cwd()]})"
        proc = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=10)
        if proc.returncode:
            raise unittest.SkipTest("pzpr is not installed; run npm --prefix puzzle/importing install")

    def test_flagged_yajilin_mirror_and_bare_imports_keep_real_clues(self) -> None:
        for url in ("yajilin/b/5/5/m32j10", "https://pzv.jp/p.html?yajilin/b/5/5/m32j10"):
            with self.subTest(url=url):
                payload = import_url(url)
                self.assertEqual(payload["instance"]["clues"]["n"], {"2,3": 2, "4,4": 0})
                self.assertEqual(payload["instance"]["clues"]["d"], {"2,3": 2, "4,4": 0})
                self.assertIn("yajilin/b/", payload["sourceUrl"])

    def test_unknown_real_slither_clue_survives_as_text(self) -> None:
        board = decode_puzzlink("slither/2/2/.")
        self.assertEqual(board.cell(0, 0).number_text, "?")
        self.assertIsNone(board.cell(0, 0).shade)

    def test_real_single_room_binds_without_missing_region_warning(self) -> None:
        payload = import_url("heyawake/2/2/004")
        self.assertEqual(payload["instance"]["clues"]["n"], {"0,0": 4})
        self.assertEqual(payload["instance"]["regions"], {"0,0": 0, "0,1": 0, "1,0": 0, "1,1": 0})
        self.assertFalse(any("no room borders" in warning for warning in payload["warnings"]))

    def test_answer_partition_does_not_become_given_regions(self) -> None:
        self.assertEqual(decode_puzzlink("shikaku/2/2/4").regions, {})
        self.assertEqual(decode_puzzlink("slither/2/2/0").regions, {})

    def test_unsupported_puzzle_reports_type_instead_of_stack_tail(self) -> None:
        with self.assertRaisesRegex(PuzzleImportError, "does not support this puzzle type: notarealtype"):
            decode_puzzlink("notarealtype/2/2/1")


if __name__ == "__main__":
    unittest.main()
