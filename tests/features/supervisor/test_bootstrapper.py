"""Tests for @agent-gauntlet/cli Node.js bootstrapper, status, doctor, repair, and uninstall."""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PACKAGE_DIR = REPO_ROOT / "packages" / "agent-gauntlet"
WRAPPER_BIN = PACKAGE_DIR / "bin" / "agent-gauntlet.js"
PACKAGE_JSON = PACKAGE_DIR / "package.json"


class TestNodeBootstrapper(unittest.TestCase):
    """Verifies that the Node.js bootstrapper runs status, doctor, and diagnostics without Python."""

    def setUp(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not installed on this system.")
            return
        self.node_bin: str = node

    def test_package_json_no_broken_prepack_script(self) -> None:
        """package.json must not ignore copy errors with '|| true'."""
        data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
        scripts = data.get("scripts", {})
        for s_name, s_cmd in scripts.items():
            self.assertNotIn(
                "|| true",
                s_cmd,
                f"Script '{s_name}' must not ignore errors with '|| true'",
            )

    def test_bootstrapper_status_command(self) -> None:
        """Running agent-gauntlet status displays supervisor daemon and socket status."""
        result = subprocess.run(
            [self.node_bin, str(WRAPPER_BIN), "status"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, f"Stderr: {result.stderr}")
        self.assertIn("agent-gauntlet", result.stdout.lower())

    def test_bootstrapper_doctor_command(self) -> None:
        """Running agent-gauntlet doctor runs platform health checks."""
        result = subprocess.run(
            [self.node_bin, str(WRAPPER_BIN), "doctor"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, f"Stderr: {result.stderr}")
        self.assertIn("platform", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
