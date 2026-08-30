"""Tests for Linux Bubblewrap sandbox runner, process isolation, and timeout handling."""

import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.supervisor.core.seams import (
    SandboxExecutionSpec,
)
from agent_gauntlet.features.supervisor.platform.linux.sandbox import BubblewrapSandboxRunner


class TestBubblewrapSandboxRunner(unittest.TestCase):
    """Verifies that BubblewrapSandboxRunner executes commands in isolated sandboxes."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp_dir.name)
        (self.workspace / "test.txt").write_text("sample content", encoding="utf-8")
        self.runner = BubblewrapSandboxRunner()

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_execute_simple_echo_command(self) -> None:
        """Executes a simple echo command and captures structured output with digest."""
        spec = SandboxExecutionSpec(
            program="echo",
            args=["hello", "world"],
            cwd=str(self.workspace),
            snapshot_dir=str(self.workspace),
            timeout_seconds=5.0,
            network_enabled=False,
            read_only_root=True,
        )
        res = self.runner.execute(spec)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("hello world", res.stdout)
        self.assertFalse(res.timed_out)
        self.assertTrue(res.stdout_digest.startswith("sha256:"))

    def test_execute_respects_timeout(self) -> None:
        """Commands exceeding timeout are terminated and marked timed_out=True."""
        spec = SandboxExecutionSpec(
            program="sleep",
            args=["5"],
            cwd=str(self.workspace),
            snapshot_dir=str(self.workspace),
            timeout_seconds=0.2,
            network_enabled=False,
            read_only_root=True,
        )
        res = self.runner.execute(spec)
        self.assertTrue(res.timed_out)
        self.assertNotEqual(res.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
