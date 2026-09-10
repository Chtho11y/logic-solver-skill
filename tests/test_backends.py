"""Backend registry and cspuz integration tests."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from puzzle.backends import (
    BackendError,
    BackendInfo,
    BackendTimeoutError,
    BackendUnavailableError,
    backend_configuration,
    backend_info,
    create_model,
    list_backends,
    normalize_backend,
    resolve_backend,
)
from puzzle.dsl.solver import (
    STATUS_COMPILED,
    STATUS_ERROR,
    STATUS_UNKNOWN,
    compile_only,
    solve,
)
from puzzle.grid import Grid
from puzzle.models import VarType, Variable


class BackendRegistryTests(unittest.TestCase):
    def test_catalogue_contains_all_supported_backends(self) -> None:
        self.assertEqual(
            [item.name for item in list_backends()],
            ["auto", "cspuz_core", "z3", "csugar", "sugar", "sugar_extended"],
        )

    def test_aliases_are_normalized(self) -> None:
        self.assertEqual(normalize_backend("AUTO"), "auto")
        self.assertEqual(normalize_backend("cspuz-core"), "cspuz_core")
        self.assertEqual(normalize_backend("sugar-ext"), "sugar_extended")

    def test_auto_prefers_core_then_falls_back_to_z3(self) -> None:
        def core_available(name: str) -> BackendInfo:
            return BackendInfo(
                name,
                name,
                name in ("cspuz_core", "z3"),
                supports_timeout=name == "z3",
            )

        with patch("puzzle.backends.registry._concrete_info", side_effect=core_available):
            self.assertEqual(resolve_backend("auto"), "cspuz_core")
            self.assertEqual(resolve_backend("auto", timeout_ms=1000), "z3")
            with self.assertRaises(BackendError):
                resolve_backend("cspuz_core", timeout_ms=1000)

        def only_z3(name: str) -> BackendInfo:
            return BackendInfo(name, name, name == "z3")

        with patch("puzzle.backends.registry._concrete_info", side_effect=only_z3):
            self.assertEqual(resolve_backend("auto"), "z3")

    def test_explicit_unavailable_backend_does_not_fallback(self) -> None:
        with patch(
            "puzzle.backends.registry._concrete_info",
            return_value=BackendInfo("cspuz_core", "cspuz_core", False, "missing"),
        ):
            with self.assertRaises(BackendUnavailableError):
                resolve_backend("cspuz_core")

    def test_native_windows_sugar_is_not_advertised(self) -> None:
        import os

        if os.name != "nt":
            self.skipTest("native Windows-specific transport check")
        info = backend_info("sugar")
        self.assertFalse(info.available)
        self.assertIn("/dev/stdin", info.reason)


class CspuzIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        if not backend_info("z3").available:
            self.skipTest("cspuz Z3 backend is not installed")

    def test_model_finds_and_reads_one_answer(self) -> None:
        model = create_model()
        value = model.Int("value", 0, 4)
        model.add_constraints(model.If(value == 3, value > 2, value < 0))
        self.assertTrue(model.find_answer("z3", 1000))
        self.assertEqual(model.value(value), 3)

    def test_each_available_primary_backend_solves(self) -> None:
        for backend in ("cspuz_core", "z3"):
            if not backend_info(backend).available:
                continue
            with self.subTest(backend=backend):
                model = create_model()
                value = model.Int("value", 0, 2)
                model.add_constraints(value == 2)
                timeout = 1000 if backend == "z3" else None
                self.assertTrue(model.find_answer(backend, timeout))
                self.assertEqual(model.value(value), 2)

    def test_backend_configuration_is_restored(self) -> None:
        import cspuz

        before = (
            cspuz.config.default_backend,
            cspuz.config.use_graph_primitive,
            cspuz.config.use_graph_division_primitive,
            cspuz.config.solver_timeout,
        )
        with backend_configuration("z3", 1234) as resolved:
            self.assertEqual(resolved, "z3")
            self.assertEqual(cspuz.config.default_backend, "z3")
            self.assertAlmostEqual(cspuz.config.solver_timeout or 0, 1.234)
        after = (
            cspuz.config.default_backend,
            cspuz.config.use_graph_primitive,
            cspuz.config.use_graph_division_primitive,
            cspuz.config.solver_timeout,
        )
        self.assertEqual(after, before)

    def test_timeout_is_reported_as_unknown(self) -> None:
        variable = Variable("x", domain=(0, 1))
        with patch(
            "puzzle.backends.cspuz.CspuzModel.find_answer",
            side_effect=BackendTimeoutError("forced timeout"),
        ):
            result = solve(
                Grid(1, 1),
                [variable],
                [],
                "x[cell(0, 0)] == 1",
                backend="z3",
            )
        self.assertEqual(result.status, STATUS_UNKNOWN)
        self.assertIn("timeout", result.message)

    def test_incomplete_model_is_reported_as_unknown(self) -> None:
        with patch("puzzle.backends.cspuz.CspuzModel.value", return_value=None):
            result = solve(
                Grid(1, 1),
                [Variable("x", domain=(0, 1))],
                [],
                "x[cell(0, 0)] == 1",
                backend="z3",
            )
        self.assertEqual(result.status, STATUS_UNKNOWN)
        self.assertIn("incomplete model", result.message)

    def test_bounded_linear_division_and_modulo(self) -> None:
        variable = Variable("x", domain=(0, 9), givens={(0, 0): 7})
        result = solve(
            Grid(1, 1),
            [variable],
            [],
            "at(x, cell(0, 0)) / 3 == 2\nat(x, cell(0, 0)) % 3 == 1",
            backend="z3",
        )
        self.assertTrue(result.ok, result.message)

    def test_large_constant_scale_compiles_without_factor_sized_allocation(self) -> None:
        result = compile_only(
            Grid(1, 1),
            [Variable("x", domain=(0, 1))],
            [],
            "1000000000 * at(x, cell(0, 0)) == 0",
        )
        self.assertEqual(result.status, STATUS_COMPILED, result.message)

    def test_boolean_broadcasting_is_not_short_circuited_to_scalar(self) -> None:
        result = solve(
            Grid(1, 1),
            [Variable("x", domain=(0, 1))],
            [],
            "count(true or [false, false]) == 2",
            backend="z3",
        )
        self.assertTrue(result.ok, result.message)

    def test_sparse_constant_component_ids_use_grid_linear_indices(self) -> None:
        result = solve(
            Grid(3, 3),
            [
                Variable(
                    "a",
                    var_type=VarType.CONSTANT,
                    givens={(2, 2): 1},
                )
            ],
            [],
            "at(cc8_size(a), cell(2, 2)) == 1",
            backend="z3",
        )
        self.assertTrue(result.ok, result.message)

    def test_unbounded_variables_are_rejected(self) -> None:
        result = compile_only(
            Grid(1, 1),
            [Variable("x", domain=None)],
            [],
            "x[cell(0, 0)] == 0",
        )
        self.assertEqual(result.status, STATUS_ERROR)
        self.assertIn("finite bounds", result.message)

    def test_old_z3_logic_name_gets_migration_error(self) -> None:
        result = solve(
            Grid(1, 1),
            [Variable("x", domain=(0, 1))],
            [],
            "x[cell(0, 0)] == 1",
            logic="QF_LIA",
        )
        self.assertEqual(result.status, STATUS_ERROR)
        self.assertIn("backend='z3'", result.message)


if __name__ == "__main__":
    unittest.main()
