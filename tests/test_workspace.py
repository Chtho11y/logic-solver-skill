"""Custom workspace definitions and independent Penpa variable documents."""
import unittest
from unittest.mock import patch

from puzzle.importing.board import LayerBoard
from puzzle.importing.penpa import encode_penpa
from puzzle.runner import solve_payload


class WorkspaceTests(unittest.TestCase):
    def payload(self):
        return {
            "instance": {"puzzle": "custom", "rows": 2, "cols": 2, "params": {"k": 3}},
            "spec": {"key": "custom", "variables": [
                {"name": name, "domain": [0, 9]} for name in ("x", "y")
            ], "layers": [
                {"id": name, "element": "number", "var": name} for name in ("x", "y")
            ]},
            "source": "x[cell(0, 0)] != y[cell(0, 0)]",
            "documents": [],
        }

    def test_same_position_different_variables_is_not_merged(self):
        payload = self.payload()
        for name, value in (("x", 1), ("y", 2)):
            board = LayerBoard(2, 2)
            board.cell(0, 0).number = value
            payload["documents"].append({"id": name, "url": encode_penpa(board)})
        with patch("puzzle.runner.solve_instance", return_value={"status": "sat"}) as solve:
            solve_payload(payload)
        instance = solve.call_args.args[1]
        self.assertEqual(instance.clues, {"x": {"0,0": 1}, "y": {"0,0": 2}})
        self.assertEqual(instance.params["k"], 3)

    def test_duplicate_names_and_unknown_bindings_are_rejected(self):
        for change in ("duplicate", "binding"):
            payload = self.payload()
            if change == "duplicate":
                payload["spec"]["variables"][1]["name"] = "x"
            else:
                payload["spec"]["layers"][0]["var"] = "missing"
            with self.assertRaises(ValueError):
                solve_payload(payload)

    def test_unbound_drawing_is_not_silently_dropped(self):
        payload = self.payload()
        board = LayerBoard(2, 2)
        board.cell(0, 0).number = 1
        payload["documents"] = [{"id": "__unbound", "url": encode_penpa(board)}]
        with self.assertRaisesRegex(ValueError, "未绑定"):
            solve_payload(payload)

    def test_drawn_cc_border_adds_constraint_without_replacing_source(self):
        payload = self.payload()
        payload["spec"]["variables"] = [{"name": "c", "type": "cc"}]
        payload["spec"]["layers"] = [{"id": "c", "element": "region", "var": "c"}]
        payload["source"] = "c.size[cell(0, 0)] >= 1"
        board = LayerBoard(2, 2)
        board.edge("V", 0, 1).line = 1
        payload["documents"] = [{"id": "c", "url": encode_penpa(board)}]
        with patch("puzzle.runner.solve_instance", return_value={"status": "sat"}) as solve:
            solve_payload(payload)
        source = solve.call_args.kwargs["source"]
        self.assertTrue(source.startswith(payload["source"]))
        self.assertIn('c.border[edge("V", 0, 1)] == 1', source)


if __name__ == "__main__":
    unittest.main()
