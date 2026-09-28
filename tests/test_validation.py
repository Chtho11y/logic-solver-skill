"""Regressions for validation exit codes and parameter binding."""
import contextlib
import io
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import verify
from puzzle.importing.bind import bind_instance, empty_outside
from puzzle.importing.board import LayerBoard
from puzzle.spec import load_spec
from tools.check import synthetic_instance


class ValidationTests(unittest.TestCase):
    def test_missing_sample_returns_nonzero_from_cli(self):
        result = subprocess.run([sys.executable, 'verify.py', 'aquapelago'],
                                cwd=Path(__file__).resolve().parent.parent,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('no sample', result.stdout)

    def test_summary_counts_failed_puzzles_not_messages(self):
        out = io.StringIO()
        with patch.object(verify, 'check', return_value=['FAIL one', 'WARN two']), contextlib.redirect_stdout(out):
            self.assertEqual(verify.main(['example']), 1)
        self.assertIn('0/1 clean', out.getvalue())

    def test_success_returns_zero(self):
        with patch.object(verify, 'check', return_value=['ok example']), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify.main(['example']), 0)

    def test_dense_domino_numbers_are_present_on_synthetic_board(self):
        instance = synthetic_instance('domino-search')
        self.assertEqual(len(instance.clues['n']), instance.rows * instance.cols)

    def test_import_does_not_infer_letter_count_from_width(self):
        for key in ('easyasabc', 'fuzuli'):
            spec = load_spec(key)
            with self.subTest(key=key):
                instance = bind_instance(LayerBoard(rows=4, cols=4), spec)
                self.assertEqual(instance['params']['k'], spec.params['defaults']['k'])

    def test_standard_skyscrapers_uses_imported_board_width(self):
        instance = bind_instance(LayerBoard(rows=3, cols=3), load_spec('skyscrapers'))
        self.assertEqual(instance['params']['k'], 3)

    def test_rectangular_outside_lengths(self):
        outside = empty_outside(3, 5)
        self.assertEqual(len(outside['right']), 3)
        self.assertEqual(len(outside['bottom']), 5)
