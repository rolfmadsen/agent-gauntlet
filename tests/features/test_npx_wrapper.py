"""Acceptance and integration tests for NPM and NPX Distribution Wrapper."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE_DIR = REPO_ROOT / "packages" / "agent-gauntlet"
WRAPPER_BIN = PACKAGE_DIR / "bin" / "agent-gauntlet.js"
PACKAGE_JSON = PACKAGE_DIR / "package.json"


class TestNpxWrapperAcceptance(unittest.TestCase):
    """Test suite for Node.js / NPX CLI wrapper."""

    def setUp(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not installed on this system.")
            return
        self.node_bin: str = node

    def test_package_json_manifest_structure(self) -> None:
        """Validates that package.json exists and has valid name and bin configuration."""
        self.assertTrue(PACKAGE_JSON.is_file(), f"Expected {PACKAGE_JSON} to exist")
        data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
        self.assertEqual(data.get("name"), "@agent-gauntlet/cli")
        self.assertIn("bin", data)
        self.assertEqual(data["bin"].get("agent-gauntlet"), "./bin/agent-gauntlet.js")
        self.assertTrue(data.get("version"), "package.json must declare a valid version")

    def test_wrapper_bin_exists_and_is_executable(self) -> None:
        """Validates that bin/agent-gauntlet.js exists."""
        self.assertTrue(WRAPPER_BIN.is_file(), f"Expected {WRAPPER_BIN} to exist")

    def test_wrapper_help_invocation(self) -> None:
        """Running node agent-gauntlet.js --help returns exit code 0 and displays help text."""
        result = subprocess.run(
            [self.node_bin, str(WRAPPER_BIN), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, f"Stderr: {result.stderr}")
        self.assertIn("agent-gauntlet", result.stdout.lower())
        self.assertIn("verify", result.stdout.lower())
        self.assertIn("init", result.stdout.lower())

    def test_wrapper_init_workspace_execution(self) -> None:
        """Running node agent-gauntlet.js init --workspace <tmp> scaffolds project files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            result = subprocess.run(
                [
                    self.node_bin,
                    str(WRAPPER_BIN),
                    "init",
                    "--workspace",
                    str(tmp_path),
                    "--stack",
                    "typescript",
                ],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
            self.assertEqual(
                result.returncode, 0, f"Stderr: {result.stderr}\nStdout: {result.stdout}"
            )
            self.assertTrue((tmp_path / "gauntlet.toml").is_file())
            self.assertTrue((tmp_path / "spec.md").is_file())
            self.assertTrue((tmp_path / "CODING_STANDARDS.md").is_file())
            self.assertTrue((tmp_path / ".agents" / "AGENTS.md").is_file())
            self.assertTrue((tmp_path / ".agents" / "skills" / "old-coder" / "SKILL.md").is_file())

    def test_wrapper_handles_missing_python(self) -> None:
        """Wrapper gracefully handles systems without Python on PATH."""
        env = {
            "PATH": "/nonexistent-bin-dir",
        }
        result = subprocess.run(
            [self.node_bin, str(WRAPPER_BIN), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Python 3", result.stderr)

    def test_wrapper_forwards_error_exit_code(self) -> None:
        """Running an invalid command through the wrapper forwards non-zero exit code."""
        result = subprocess.run(
            [self.node_bin, str(WRAPPER_BIN), "invalid-command-xyz"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
