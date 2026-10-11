"""Regression for the user's native-outline Penpa URL and typed cage documents."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from puzzle.importing import PuzzleImportError, decode_penpa, encode_penpa, import_url
from puzzle.importing.bind import bind_instance
from puzzle.importing.board import LayerBoard, from_layers_json
from puzzle.importing.penpa import _compress, _deflate, _expand, _inflate, parse_penpa_payload, PenpaGrid
from puzzle.runner import solve_payload
from puzzle.spec import PuzzleSpec

FIXTURE = Path(__file__).parent / 'fixtures' / 'imports' / 'killer-cages.penpa.url'
TOTALS = {'0,0': 4, '1,2': 3, '1,3': 3, '2,0': 100, '3,3': 52}
GROUPS = [
    {'0,0', '0,1', '0,2', '0,3', '1,0'},
    {'1,2', '2,2', '3,2'},
    {'1,3', '2,3'},
    {'2,0', '3,0', '4,0', '4,1'},
    {'3,3', '3,4', '4,3'},
]


def groups(mapping):
    return {frozenset(k for k, v in mapping.items() if v == group) for group in set(mapping.values())}


def mutate_question(url, change):
    parts = _expand(_inflate(parse_penpa_payload(url)['p'])).split('\n')
    question = json.loads(parts[3])
    change(question)
    parts[3] = _compress(json.dumps(question))
    return '#m=edit&p=' + _deflate('\n'.join(parts))


def spec_json():
    return {'key': 'custom', 'variables': [
        {'name': 'cage_regions', 'kind': 'cell', 'type': 'constant'},
        {'name': 'cage_totals', 'kind': 'cell', 'type': 'constant'},
    ], 'layers': [
        {'id': 'cages', 'element': 'region', 'var': 'cage_regions', 'options': {'semantic': 'cage-region'}},
        {'id': 'totals', 'element': 'number', 'var': 'cage_totals', 'options': {'semantic': 'cage-total', 'placement': 'corner'}},
    ]}


class NativeCageTests(unittest.TestCase):
    def setUp(self):
        self.url = FIXTURE.read_text().strip()

    def test_exact_user_url_recovers_five_sparse_cages_and_totals(self):
        board = decode_penpa(self.url)
        self.assertEqual((board.rows, board.cols), (5, 5))
        self.assertEqual(groups(board.cages), set(map(frozenset, GROUPS)))
        self.assertEqual(board.corner_numbers, TOTALS)
        self.assertEqual(len(board.cages), 17)
        self.assertNotIn('4,4', board.cages)
        self.assertFalse(board.regions)
        self.assertEqual(board.warnings, [])
        payload = import_url(self.url)
        self.assertEqual({l['id'] for l in payload['layers']}, {'cage_regions', 'cage_totals'})
        self.assertIsNone(payload['instance'])  # Importing elements must not invent puzzle rules.

    def test_cages_survive_generic_and_native_roundtrip(self):
        original = decode_penpa(self.url)
        rebuilt = from_layers_json(5, 5, original.to_layers_json())
        roundtrip = decode_penpa(encode_penpa(rebuilt))
        self.assertEqual(groups(roundtrip.cages), groups(original.cages))
        self.assertEqual(roundtrip.corner_numbers, TOTALS)
        self.assertFalse(roundtrip.warnings)

    def test_cages_and_regular_regions_are_independent(self):
        board = decode_penpa(self.url)
        board.edge('V', 0, 1).line = 1
        again = decode_penpa(encode_penpa(board))
        self.assertTrue(again.regions)
        self.assertEqual(groups(again.cages), groups(board.cages))
        bound = bind_instance(again, PuzzleSpec.from_json(spec_json()))
        self.assertEqual(groups(bound['clues']['cage_regions']), groups(board.cages))
        self.assertEqual(bound['clues']['cage_totals'], TOTALS)

    def test_totals_and_normal_numbers_bind_independently_in_any_layer_order(self):
        board = decode_penpa(self.url)
        board.cell(4, 4).number = 9
        data = spec_json()
        data['variables'].append({'name': 'given', 'kind': 'cell', 'type': 'constant'})
        data['layers'].append({'id': 'given', 'element': 'number', 'var': 'given'})
        for layers in (data['layers'], list(reversed(data['layers']))):
            bound = bind_instance(board, PuzzleSpec.from_json({**data, 'layers': layers}))
            self.assertEqual(bound['clues']['given'], {'4,4': 9})
            self.assertEqual(bound['clues']['cage_totals'], TOTALS)

    def test_inferred_preset_binding_failure_still_returns_decoded_layers(self):
        data = spec_json()
        data['variables'][0]['type'] = 'cc'
        with patch('puzzle.importing.resolve_puzzle_key', return_value='custom'), patch('puzzle.importing.load_spec', return_value=PuzzleSpec.from_json(data)):
            result = import_url(self.url, puzzle='custom')
        self.assertIsNone(result['instance'])
        self.assertEqual(len(result['layers']), 2)
        self.assertTrue(any('variable mapping' in warning for warning in result['warnings']))

    def test_separate_documents_bind_constant_types_without_filling_uncaged_cells(self):
        cages = decode_penpa(self.url)
        totals = LayerBoard(5, 5, corner_numbers=cages.corner_numbers)
        cages.corner_numbers = {}
        payload = {
            'spec': spec_json(), 'instance': {'puzzle': 'custom', 'rows': 5, 'cols': 5},
            'source': '', 'documents': [
                {'id': 'cage_regions', 'url': encode_penpa(cages)},
                {'id': 'cage_totals', 'url': encode_penpa(totals)},
            ],
        }
        with patch('puzzle.runner.solve_instance', return_value={'status': 'compiled'}) as solve:
            solve_payload(payload)
        instance = solve.call_args.args[1]
        self.assertEqual(groups(instance.clues['cage_regions']), set(map(frozenset, GROUPS)))
        self.assertEqual(instance.clues['cage_totals'], TOTALS)
        self.assertNotIn('4,4', instance.clues['cage_regions'])

    def test_open_cage_is_actionable_error(self):
        url = mutate_question(self.url, lambda q: q['cage'].pop('404,405'))
        with self.assertRaisesRegex(PuzzleImportError, 'open or branched'):
            decode_penpa(url)

    def test_conflicting_explicit_membership_is_rejected(self):
        url = mutate_question(self.url, lambda q: q.update(killercages=[[20]]))
        with self.assertRaisesRegex(PuzzleImportError, 'disagree'):
            decode_penpa(url)

    def test_unbound_corner_or_cage_data_cannot_silently_disappear(self):
        for board in (LayerBoard(2, 2, cages={'0,0': 0}), LayerBoard(2, 2, corner_numbers={'0,0': 8})):
            with self.assertRaisesRegex(ValueError, '未绑定'):
                solve_payload({'spec': {'key': 'custom'}, 'instance': {'puzzle': 'custom', 'rows': 2, 'cols': 2},
                               'documents': [{'id': '__unbound', 'url': encode_penpa(board)}]})


class PenpaRobustnessTests(unittest.TestCase):
    def test_pasted_query_and_hash_forms(self):
        board = LayerBoard(2, 2)
        board.cell(0, 0).number = 7
        url = encode_penpa(board)
        payload = parse_penpa_payload(url)['p']
        for url in ('p=' + payload, '#p=' + payload, '?m=edit&p=' + payload,
                    'https://example.test/editor?p=' + payload + '#m=solve'):
            self.assertEqual(decode_penpa(url).cell(0, 0).number, 7)

    def test_missing_or_invalid_payload_is_rejected(self):
        for url in ('https://example.test/penpa/#m=solve', 'p=%%%'):
            with self.assertRaises(PuzzleImportError):
                decode_penpa(url)
        with self.assertRaisesRegex(PuzzleImportError, 'conflicting'):
            decode_penpa('m=edit&p=abc&p=def')

    def test_invalid_problem_json_does_not_become_empty_board(self):
        parts = _expand(_inflate(parse_penpa_payload(encode_penpa(LayerBoard(2, 2)))['p'])).split('\n')
        parts[3] = '{broken'
        with self.assertRaisesRegex(PuzzleImportError, 'problem data'):
            decode_penpa('p=' + _deflate('\n'.join(parts)))

    def test_generic_string_number_preserves_list_clues(self):
        board = from_layers_json(2, 2, [{'element': 'number', 'values': {'0,0': '1 2 ?'}}])
        self.assertEqual(decode_penpa(encode_penpa(board)).cell(0, 0).number_text, '1 2 ?')

    def test_other_symbols_and_center_links_are_not_lost(self):
        for symbol in ('tent', 'ship', 'wave', 'bulb', 'square', 'triangle', 'tree'):
            board = LayerBoard(2, 2)
            setattr(board.cell(0, 0), symbol, 1)
            self.assertIn(symbol, {l['element'] for l in board.to_layers_json()})
            self.assertEqual(getattr(decode_penpa(encode_penpa(board)).cell(0, 0), symbol), 1)
        board = LayerBoard(2, 2)
        board.edge('V', 0, 1).link = 1
        board.edge('H', 1, 0).dot = 2
        again = decode_penpa(encode_penpa(board))
        self.assertEqual(again.edge('V', 0, 1).link, 1)
        self.assertEqual(again.edge('H', 1, 0).dot, 2)

    def test_dot_positions_match_native_edge_midpoints_with_margins(self):
        grid = PenpaGrid(3, 5, 1, 2, 2, 1)
        area = grid.real_rows * grid.real_cols
        # Penpa type 2 lies below its cell; type 3 lies to the right.
        h_index = 2 * area + (2 + 1 + grid.top) * grid.real_cols + 4 + 2 + grid.left
        v_index = 3 * area + (1 + 2 + grid.top) * grid.real_cols + 3 + 1 + grid.left
        self.assertEqual(grid.decode_index(h_index), ('edge', ('H', 2, 4)))
        self.assertEqual(grid.decode_index(v_index), ('edge', ('V', 1, 3)))
        board = LayerBoard(3, 5)
        board.edge('H', 2, 4).dot = 1
        board.edge('V', 1, 3).dot = 2
        parts = _expand(_inflate(parse_penpa_payload(encode_penpa(board))['p'])).split('\n')
        symbols = json.loads(parts[3])['symbol']
        # No-margin native board has width 9, height 7, area 63.
        self.assertEqual(symbols[str(2 * 63 + 3 * 9 + 6)][0], 1)
        self.assertEqual(symbols[str(3 * 63 + 3 * 9 + 4)][0], 2)

    def test_both_diagonal_directions_survive_native_and_generic_roundtrip(self):
        board = LayerBoard(2, 2)
        board.cell(0, 0).diagonal = 1
        board.cell(1, 1).diagonal = 2
        rebuilt = from_layers_json(2, 2, board.to_layers_json())
        decoded = decode_penpa(encode_penpa(rebuilt))
        self.assertEqual(decoded.cell(0, 0).diagonal, 1)
        self.assertEqual(decoded.cell(1, 1).diagonal, 2)
        self.assertFalse(decoded.edges)
        self.assertFalse(decoded.regions)
        spec = PuzzleSpec.from_json({'key': 'custom', 'variables': [{'name': 'd', 'type': 'constant'}],
                                   'layers': [{'id': 'd', 'element': 'diagonal', 'var': 'd'}]})
        self.assertEqual(bind_instance(decoded, spec)['clues']['d'], {'0,0': 1, '1,1': 2})

    def test_overlapping_diagonals_reject_instead_of_losing_one(self):
        board = LayerBoard(2, 2)
        board.cell(0, 0).diagonal = 1
        # On a 2×2 board, native corner indices TL/TR/BL/BR are 43/44/49/50.
        url = mutate_question(encode_penpa(board), lambda q: q['lineE'].update({'44,49': 2}))
        with self.assertRaisesRegex(PuzzleImportError, 'Both diagonals'):
            decode_penpa(url)

    def test_plain_number_binding_rejects_text_instead_of_dropping_it(self):
        board = LayerBoard(2, 2)
        board.cell(0, 0).number_text = '?'
        spec = PuzzleSpec.from_json({'key': 'custom', 'variables': [{'name': 'n', 'type': 'constant'}],
                                   'layers': [{'id': 'n', 'element': 'number', 'var': 'n'}]})
        with self.assertRaisesRegex(PuzzleImportError, 'not an integer'):
            bind_instance(board, spec)

    def test_multiple_number_bindings_require_explicit_documents(self):
        board = LayerBoard(2, 2)
        board.cell(0, 0).number = 4
        spec = PuzzleSpec.from_json({'key': 'custom', 'variables': [{'name': n, 'type': 'constant'} for n in ('a', 'b')],
                                   'layers': [{'id': n, 'element': 'number', 'var': n} for n in ('a', 'b')]})
        with self.assertRaisesRegex(PuzzleImportError, 'match both'):
            bind_instance(board, spec)


if __name__ == '__main__':
    unittest.main()
