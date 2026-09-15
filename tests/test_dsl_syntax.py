"""Lexer/parser regression tests (no solver backend required)."""

from __future__ import annotations

import unittest

from puzzle.dsl.errors import LexError, ParseError
from puzzle.dsl.lexer import tokenize
from puzzle.dsl.parser import parse
from puzzle.dsl.tokens import T_DEDENT, T_EOF, T_NEWLINE


class ContinuationLineTests(unittest.TestCase):
    def test_a_closed_continuation_ends_its_logical_line(self) -> None:
        sources = {
            "statement follows": "let a = [\n    1\n]\ntrue\n",
            "inside a block": "if true:\n    let a = [\n        1,\n        2\n    ]\n    count(a) == 2\ntrue\n",
            "nested brackets": "let a = count([\n    1,\n    (2 +\n     3)\n])\na == 2\n",
            "trailing comment": "let a = [\n    1\n]  # done\ntrue\n",
            "no trailing newline": "let a = [\n    1\n]\ntrue",
            "call arguments": "let a = count(\n    [1, 2]\n)\na == 2\n",
        }
        for label, source in sources.items():
            with self.subTest(label=label):
                self.assertEqual(len(parse(source).statements), 2)

    def test_open_brackets_keep_the_logical_line_alive(self) -> None:
        tokens = tokenize("let a = [\n    1,\n    2\n]\n")
        newlines = [token for token in tokens if token.type == T_NEWLINE]
        self.assertEqual(len(newlines), 1)
        self.assertEqual(newlines[0].line, 4)

    def test_no_duplicate_newline_and_dedents_come_last(self) -> None:
        tokens = tokenize("if true:\n    let a = [\n        1\n    ]\n")
        kinds = [token.type for token in tokens]
        self.assertEqual(kinds[-3:], [T_NEWLINE, T_DEDENT, T_EOF])
        self.assertNotIn((T_NEWLINE, T_NEWLINE), list(zip(kinds, kinds[1:])))

    def test_unterminated_bracket_is_reported_by_the_parser(self) -> None:
        with self.assertRaises(ParseError):
            parse("let a = [\n    1\n")


class SuiteTests(unittest.TestCase):
    def test_inline_suite_accepts_a_single_statement(self) -> None:
        self.assertEqual(len(parse("if true: true\n").statements), 1)

    def test_inline_else_on_the_same_line_is_not_supported(self) -> None:
        with self.assertRaises(ParseError):
            parse("if true: true else: false\n")

    def test_empty_block_is_rejected(self) -> None:
        with self.assertRaises(ParseError):
            parse("if true:\ntrue\n")


class LexicalErrorTests(unittest.TestCase):
    def test_inconsistent_indentation(self) -> None:
        with self.assertRaises(LexError):
            parse("if true:\n        true\n    false\n")

    def test_unterminated_string(self) -> None:
        with self.assertRaises(LexError):
            tokenize('import "core\n')


if __name__ == "__main__":
    unittest.main()
