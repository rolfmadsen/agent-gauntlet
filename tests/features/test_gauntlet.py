"""Black-box acceptance tests for features/run_gauntlet."""

import sys
import unittest
from pathlib import Path

from agent_gauntlet.features.gauntlet import (
    GauntletReport,
    LayerDefinition,
    LayerResult,
    run_gauntlet,
)


class TestRunGauntletAcceptance(unittest.TestCase):
    """Sort-boks accepttests for features/run_gauntlet."""

    def test_run_gauntlet_empty_layers_raises_value_error(self) -> None:
        """Scenario: Running gauntlet with zero layers raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            run_gauntlet([])
        self.assertIn("at least one verification layer", str(ctx.exception).lower())

    def test_run_gauntlet_all_layers_pass(self) -> None:
        """Scenario: All verification layers exit with code 0."""
        layers = [
            LayerDefinition(
                name="lint",
                command=[sys.executable, "-c", "import sys; print('lint clean'); sys.exit(0)"],
            ),
            LayerDefinition(
                name="types",
                command=[sys.executable, "-c", "import sys; print('types clean'); sys.exit(0)"],
            ),
        ]
        report = run_gauntlet(layers)

        self.assertIsInstance(report, GauntletReport)
        self.assertTrue(report.success)
        self.assertEqual(len(report.layers), 2)
        self.assertTrue(all(layer.passed for layer in report.layers))
        self.assertTrue(all(layer.exit_code == 0 for layer in report.layers))
        self.assertIn("lint clean", report.layers[0].output)
        self.assertIn("types clean", report.layers[1].output)
        self.assertGreaterEqual(report.total_duration_seconds, 0.0)

    def test_run_gauntlet_fail_fast_on_broken_layer(self) -> None:
        """Scenario: Multi-layer runner halts immediately when a layer fails."""
        layers = [
            LayerDefinition(
                name="layer-1-pass",
                command=[sys.executable, "-c", "import sys; sys.exit(0)"],
            ),
            LayerDefinition(
                name="layer-2-fail",
                command=[sys.executable, "-c", "import sys; sys.exit(1)"],
            ),
            LayerDefinition(
                name="layer-3-never-reached",
                command=[sys.executable, "-c", "import sys; sys.exit(0)"],
            ),
        ]
        report = run_gauntlet(layers)

        self.assertIsInstance(report, GauntletReport)
        self.assertFalse(report.success, "Gauntlet must report failure when a mandatory layer fails")
        self.assertEqual(
            len(report.layers),
            2,
            "Gauntlet must halt on first broken mandatory layer without executing subsequent layers",
        )
        self.assertTrue(report.layers[0].passed)
        self.assertEqual(report.layers[0].exit_code, 0)
        self.assertFalse(report.layers[1].passed)
        self.assertEqual(report.layers[1].exit_code, 1)

    def test_run_gauntlet_optional_layer_failure_does_not_halt(self) -> None:
        """Scenario: Optional layer failure is recorded but does not abort subsequent layers or fail gauntlet."""
        layers = [
            LayerDefinition(
                name="opt-advisory-layer",
                command=[sys.executable, "-c", "import sys; print('advisory warning'); sys.exit(2)"],
                optional=True,
            ),
            LayerDefinition(
                name="mandatory-layer",
                command=[sys.executable, "-c", "import sys; print('core passed'); sys.exit(0)"],
                optional=False,
            ),
        ]
        report = run_gauntlet(layers)

        self.assertIsInstance(report, GauntletReport)
        self.assertTrue(report.success, "Optional layer failure must not fail overall gauntlet")
        self.assertEqual(len(report.layers), 2)
        self.assertFalse(report.layers[0].passed)
        self.assertEqual(report.layers[0].exit_code, 2)
        self.assertTrue(report.layers[1].passed)
        self.assertEqual(report.layers[1].exit_code, 0)

    def test_run_gauntlet_nonexistent_command_fails_closed(self) -> None:
        """Scenario: Invalid or nonexistent command fails closed without unhandled crash."""
        layers = [
            LayerDefinition(
                name="broken-executable",
                command=["/path/to/nonexistent/executable/binary/test_xyz"],
            )
        ]
        report = run_gauntlet(layers)

        self.assertIsInstance(report, GauntletReport)
        self.assertFalse(report.success)
        self.assertEqual(len(report.layers), 1)
        self.assertFalse(report.layers[0].passed)
        self.assertNotEqual(report.layers[0].exit_code, 0)


if __name__ == "__main__":
    unittest.main()
