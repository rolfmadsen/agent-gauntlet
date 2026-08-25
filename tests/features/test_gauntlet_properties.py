"""Property-based and invariant tests for run_gauntlet."""

import sys
import unittest
from pathlib import Path

from agent_gauntlet.features.gauntlet import (
    LayerDefinition,
    run_gauntlet,
)


class TestRunGauntletInvariants(unittest.TestCase):
    """Invariants for gauntlet verification runner."""

    def test_timeout_fails_closed_and_halts(self) -> None:
        """Invariant: Layer that exceeds timeout is killed and halts mandatory pipeline."""
        layers = [
            LayerDefinition(
                name="timeout-layer",
                command=[sys.executable, "-c", "import time; time.sleep(10)"],
                timeout_seconds=0.2,
                optional=False,
            ),
            LayerDefinition(
                name="unreachable",
                command=[sys.executable, "-c", "import sys; sys.exit(0)"],
            ),
        ]
        report = run_gauntlet(layers)

        self.assertFalse(report.success)
        self.assertEqual(len(report.layers), 1)
        self.assertEqual(report.layers[0].exit_code, 124)
        self.assertFalse(report.layers[0].passed)
        self.assertIn("timed out", report.layers[0].output.lower())

    def test_respects_custom_cwd(self) -> None:
        """Invariant: Commands execute within specified cwd."""
        target_dir = Path(__file__).resolve().parent.parent.parent / "src"
        layers = [
            LayerDefinition(
                name="check-cwd",
                command=[sys.executable, "-c", "import os; print(os.getcwd())"],
            )
        ]
        report = run_gauntlet(layers, cwd=target_dir)

        self.assertTrue(report.success)
        self.assertEqual(len(report.layers), 1)
        self.assertIn(str(target_dir), report.layers[0].output.strip())

    def test_gauntlet_duration_is_monotonic(self) -> None:
        """Invariant: Total duration >= sum of individual layer durations."""
        layers = [
            LayerDefinition(
                name="step-1",
                command=[sys.executable, "-c", "import sys; sys.exit(0)"],
            ),
            LayerDefinition(
                name="step-2",
                command=[sys.executable, "-c", "import sys; sys.exit(0)"],
            ),
        ]
        report = run_gauntlet(layers)

        sum_durations = sum(layer.duration_seconds for layer in report.layers)
        self.assertGreaterEqual(report.total_duration_seconds, 0.0)
        self.assertGreaterEqual(report.total_duration_seconds + 0.01, sum_durations)


if __name__ == "__main__":
    unittest.main()
