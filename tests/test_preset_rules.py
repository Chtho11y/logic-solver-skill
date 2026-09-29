"""Rule counterexamples and small exhaustive checks against independent oracles."""
import itertools
import unittest

from puzzle.backends.cspuz import CspuzModel
from puzzle.dsl.patterns import cyclic_run_masks
from puzzle.dsl.solver import solve
from puzzle.grid import Grid
from puzzle.models import Variable
from puzzle.spec import make_loader
from puzzle.importing.puzzlink import layerboard_from_pzpr
from puzzle.importing.bind import bind_instance
from puzzle.importing.board import LayerBoard
from puzzle.importing.penpa import encode_penpa, decode_penpa, PenpaGrid, _decode_number
from puzzle.runner import solve_instance
from puzzle.spec import Instance, PuzzleSpec, load_spec


def components(n, edges, selected):
    remaining, groups = set(selected), []
    while remaining:
        group = {remaining.pop()}
        todo = list(group)
        while todo:
            u = todo.pop()
            for a, b in edges:
                v = b if a == u else a if b == u else None
                if v in remaining:
                    remaining.remove(v)
                    group.add(v)
                    todo.append(v)
        groups.append(group)
    return groups


class PresetRuleTests(unittest.TestCase):
    def solve_board(self, key, rows, clues=None, regions=None):
        given = {f"{r},{c}": int(v) for r, row in enumerate(rows) for c, v in enumerate(row)}
        return solve_instance(load_spec(key), Instance(key, len(rows), len(rows[0]),
            {"x": given, **(clues or {})}, regions or {}), backend="z3")

    def test_tapa_number_changes_validity(self):
        board = ["111", "001", "000"]
        for clue, status in [(4, "sat"), ([4], "sat"), ([3], "unsat"), ([-1], "sat"), ([2, 2], "unsat")]:
            with self.subTest(clue=clue):
                result = self.solve_board("tapa", board, {"n": {"1,1": clue}})
                self.assertEqual(result["status"], status, result)

    def test_tapa_zero_and_question_mark(self):
        for clue in ([0], [-1], [1], [-1, -1]):
            result = self.solve_board("tapa", ["000", "000", "000"], {"n": {"1,1": clue}})
            self.assertEqual(result["status"], "sat" if len(clue) == 1 and clue[0] <= 0 else "unsat", result)

    def test_square_rejects_rectangle(self):
        self.assertEqual(self.solve_board("circlesquare", ["000", "111"])["status"], "unsat")
        result = self.solve_board("circlesquare", ["001", "001"])
        self.assertEqual(result["status"], "sat", result)

    def test_oneroom_cannot_connect_through_other_rooms(self):
        regions = {"0,0": 0, "0,1": 0, "0,2": 0, "1,0": 1, "1,1": 2, "1,2": 3}
        self.assertEqual(self.solve_board("oneroom", ["010", "000"], regions=regions)["status"], "unsat")
        result = self.solve_board("oneroom", ["000", "000"], regions=regions)
        self.assertEqual(result["status"], "sat", result)

    def test_run_clues_survive_penpa_roundtrip(self):
        board = LayerBoard(3, 3)
        board.cell(1, 1).number_text = "1 2 ?"
        bound = bind_instance(decode_penpa(encode_penpa(board)), load_spec("tapa"))
        self.assertEqual(bound["clues"]["n"]["1,1"], [1, 2, -1])

    def test_invalid_run_text_is_rejected(self):
        for text in ("12", "0 1", "a", "9", "1 1 1 1 1"):
            board = LayerBoard(3, 3)
            board.cell(1, 1).number_text = text
            with self.subTest(text=text), self.assertRaises(ValueError):
                bind_instance(board, load_spec("tapa"))

    def test_native_tapa_and_puzzlink_multiclues(self):
        board = LayerBoard(3, 3)
        grid = PenpaGrid(3, 3, 0, 0, 0, 0)
        _decode_number(board, grid, {str(grid.cell_index(1, 1)): ["12?", 1, "4"]})
        self.assertEqual(bind_instance(board, load_spec("tapa"))["clues"]["n"]["1,1"], [1, 2, -1])
        board = layerboard_from_pzpr({"pid": "tapa", "rows": 3, "cols": 3,
            "cells": [{"r": 1, "c": 1, "qnums": [1, 2, -2]}]})
        self.assertEqual(bind_instance(board, load_spec("tapa"))["clues"]["n"]["1,1"], [1, 2, -1])


class CommonShapeTests(unittest.TestCase):
    def check(self, board, constraint, expected):
        givens = {(r, c): int(v) for r, row in enumerate(board) for c, v in enumerate(row)}
        result = solve(Grid(len(board), len(board[0])), [Variable("x", domain=(0, 1), givens=givens)],
                       [], constraint, backend="z3", loader=make_loader())
        self.assertEqual(result.status, expected, result.message)

    def test_translations_and_rotations(self):
        board = ["1100", "0001", "0001"]
        self.check(board, "same_shape(x, cell(0,0), cell(1,3))", "sat")
        self.check(board, "same_shape(x, cell(0,0), cell(1,3), false, false)", "unsat")
        self.check(board, "not same_shape(x, cell(0,0), cell(1,3))", "unsat")

    def test_equal_area_does_not_mean_same_shape(self):
        self.check(["11100", "00011", "00010"], "same_shape(x, cell(0,0), cell(1,4))", "unsat")

    def test_subset_is_not_congruence(self):
        self.check(["11011", "00001"], "same_shape(x, cell(0,0), cell(0,3))", "unsat")

    def test_reflection_option(self):
        board = ["10001", "10001", "11011"]
        self.check(board, "same_shape(x, cell(0,0), cell(0,4), true, true)", "sat")
        self.check(board, "same_shape(x, cell(0,0), cell(0,4), true, false)", "unsat")

    def test_contacts_count_groups_not_points(self):
        # The single white component touches both black components many times.
        board = ["1100", "0010", "0000"]
        self.check(board, "cc_contacts(x, cell(0,0), 0) == 1", "sat")
        self.check(board, "cc_contacts(x, cell(0,0), 1) == 1", "sat")
        self.check(board, "cc_contacts(x, cell(0,0), 1, false) == 0", "sat")

    def test_unordered_linear_runs_do_not_join_endpoints(self):
        self.check(["11011"], "unordered_runs(x[row(0)], [2,2])", "sat")
        self.check(["11011"], "cyclic_runs(x[row(0)], [4])", "sat")
        self.check(["11011"], "unordered_runs(x[row(0)], [4])", "unsat")

    def test_partial_metadata_roundtrip_and_result(self):
        spec = load_spec("akichi")
        self.assertTrue(spec.partial)
        self.assertTrue(PuzzleSpec.from_json(spec.to_json()).partial)
        self.assertEqual(PuzzleSpec.from_json(spec.to_json()).unencoded_clues, spec.unencoded_clues)
        result = solve_instance(spec, Instance("akichi", 1, 1), backend="z3", source="true")
        self.assertTrue(result["partial"])
        self.assertTrue(result["sourceModified"])


class ExhaustiveGraphTests(unittest.TestCase):
    def test_vertex_connectivity_all_two_by_three_boards(self):
        edges = [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)]
        for bits in itertools.product((False, True), repeat=6):
            model = CspuzModel("z3")
            model.add_constraints(model.vertices_connected(bits, edges))
            expected = len(components(6, edges, [i for i, bit in enumerate(bits) if bit])) <= 1
            self.assertEqual(model.find_answer("z3"), expected, bits)

    def test_single_cycle_all_square_edge_subsets(self):
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
        for bits in itertools.product((False, True), repeat=4):
            for nonempty in (False, True):
                model = CspuzModel("z3")
                model.add_constraints(model.edges_single_cycle(bits, edges, 4, nonempty=nonempty))
                self.assertEqual(model.find_answer("z3"), all(bits) or (not nonempty and not any(bits)), (bits, nonempty))

    def test_division_sizes_and_redundant_borders(self):
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
        for borders in itertools.product((False, True), repeat=4):
            groups = components(4, [e for e, b in zip(edges, borders) if not b], range(4))
            ids = {v: i for i, group in enumerate(groups) for v in group}
            valid = all(b == (ids[u] != ids[v]) for (u, v), b in zip(edges, borders))
            sizes = [len(groups[ids[v]]) for v in range(4)]
            for wrong in (False, True):
                model = CspuzModel("z3")
                values = [model.Int(str(i), n, n) for i, n in enumerate(sizes)]
                if wrong:
                    values[0] = model.Int("wrong", 5, 5)
                model.add_constraints(model.graph_division(values, edges, borders))
                self.assertEqual(model.find_answer("z3"), valid and not wrong, (borders, wrong))

    def test_helpers_do_not_post_before_guard(self):
        model = CspuzModel("z3")
        bad = model.vertices_connected([True, False, True], [(0, 1), (1, 2)])
        self.assertEqual(model.solver.constraints, [])
        model.add_constraints(model.Implies(False, bad))
        self.assertTrue(model.find_answer("z3"))

    def test_cyclic_runs_all_neighbourhoods(self):
        edges = [(i, (i + 1) % 8) for i in range(8)]
        for mask in range(256):
            selected = [i for i in range(8) if mask & (1 << i)]
            groups = components(8, edges, selected)
            lengths = tuple(sorted(map(len, groups))) or (0,)
            self.assertIn(mask, cyclic_run_masks(8, lengths))
            for clue in ((1,), (2, 2), (1, 1, 1, 1), (0,), (-1,), (1, -1)):
                sizes = list(map(len, groups))
                if not sizes:
                    expected = clue in ((0,), (-1,))
                else:
                    expected = len(sizes) == len(clue)
                    for n in clue:
                        if n != -1:
                            if n in sizes:
                                sizes.remove(n)
                            else:
                                expected = False
                self.assertEqual(mask in cyclic_run_masks(8, clue), expected, (mask, clue))


if __name__ == "__main__":
    unittest.main()
