"""Black-box acceptance tests for agent_gauntlet.cli."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_gauntlet.cli import main
from agent_gauntlet.features.evidence import (
    CheckSummary,
    EvidenceAuthority,
    EvidenceRecord,
    compute_source_state,
)


class TestCliAcceptance(unittest.TestCase):
    """Sort-boks accepttests for agent_gauntlet CLI."""

    def setUp(self) -> None:
        self.workspace = Path(__file__).resolve().parent.parent

    def test_init_command_creates_toml(self) -> None:
        """Scenario CLI-INIT: init creates gauntlet.toml in workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["init", "-w", tmpdir, "--stack", "python"])
            self.assertEqual(exit_code, 0)
            created_file = Path(tmpdir) / "gauntlet.toml"
            self.assertTrue(created_file.exists())
            self.assertIn('stack = "python"', created_file.read_text())
            self.assertTrue((Path(tmpdir) / "CONTEXT.md").exists())
            self.assertTrue((Path(tmpdir) / "spec.md").exists())
            self.assertTrue((Path(tmpdir) / "tasks/001-bootstrap.md").exists())
            self.assertTrue((Path(tmpdir) / ".agents/AGENTS.md").exists())
            self.assertTrue((Path(tmpdir) / ".agents/hooks.json").exists())

    def test_init_command_creates_json(self) -> None:
        """Scenario CLI-INIT-JSON: init creates gauntlet.json in workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["init", "-w", tmpdir, "--stack", "typescript", "--format", "json"])
            self.assertEqual(exit_code, 0)
            created_file = Path(tmpdir) / "gauntlet.json"
            self.assertTrue(created_file.exists())
            self.assertIn('"stack": "typescript"', created_file.read_text())

    def test_tree_hash_command(self) -> None:
        """Scenario CLI-01: tree-hash prints tree hash and returns 0."""
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["tree-hash", "-w", str(self.workspace)])

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue().strip()
        self.assertGreaterEqual(len(output), 16)
        _, _, expected_tree = compute_source_state(self.workspace)
        self.assertEqual(output, expected_tree)

    def test_check_evidence_valid(self) -> None:
        """Scenario CLI-02: check-evidence verifies valid signature and tree match."""
        _, _, current_tree = compute_source_state(self.workspace)
        authority = EvidenceAuthority()
        record = EvidenceRecord(
            task_id="task-cli-valid",
            status="PASSED",
            source_tree_hash=current_tree,
            checks=[CheckSummary(name="unit-tests", passed=True, exit_code=0)],
            timestamp=1700000000.0,
        )
        signed = authority.sign_record(record)

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write(authority.generate_evidence_json(signed))
            temp_path = f.name

        try:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["check-evidence", "-w", str(self.workspace), "--evidence-file", temp_path])
            self.assertEqual(exit_code, 0)
            self.assertIn("VALID", stdout.getvalue().upper())
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_check_evidence_tampered_fails(self) -> None:
        """Scenario CLI-03a: check-evidence fails on tampered signature."""
        _, _, current_tree = compute_source_state(self.workspace)
        authority = EvidenceAuthority()
        record = EvidenceRecord(
            task_id="task-cli-tampered",
            status="FAILED",
            source_tree_hash=current_tree,
            checks=[CheckSummary(name="unit-tests", passed=False, exit_code=1)],
            timestamp=1700000000.0,
        )
        signed = authority.sign_record(record)
        # Tamper status while keeping old signature
        tampered_data = json.loads(authority.generate_evidence_json(signed))
        tampered_data["status"] = "PASSED"

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(tampered_data, f)
            temp_path = f.name

        try:
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["check-evidence", "-w", str(self.workspace), "--evidence-file", temp_path])
            self.assertEqual(exit_code, 1)
            self.assertIn("signature is invalid", stderr.getvalue().lower())
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_check_evidence_drifted_fails(self) -> None:
        """Scenario CLI-03b: check-evidence fails on mismatched tree hash."""
        authority = EvidenceAuthority()
        record = EvidenceRecord(
            task_id="task-cli-drifted",
            status="PASSED",
            source_tree_hash="deadbeef00000000",  # Different tree hash
            checks=[CheckSummary(name="unit-tests", passed=True, exit_code=0)],
            timestamp=1700000000.0,
        )
        signed = authority.sign_record(record)

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write(authority.generate_evidence_json(signed))
            temp_path = f.name

        try:
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["check-evidence", "-w", str(self.workspace), "--evidence-file", temp_path])
            self.assertEqual(exit_code, 1)
            self.assertIn("drift detected", stderr.getvalue().lower())
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_verify_command_pass(self) -> None:
        """Scenario CLI-04: verify runs layers and returns 0 on success."""
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "verify",
                    "-w",
                    str(self.workspace),
                    "--task-id",
                    "test-verify-run",
                    "--test-target",
                    "tests.features.test_gauntlet",
                ]
            )
        self.assertEqual(exit_code, 0)
        self.assertIn("PASSED", stdout.getvalue().upper())

    def test_verify_diagnostics_json(self) -> None:
        """Scenario CLI-05: verify with --diagnostics-json outputs structured json."""
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "verify",
                    "-w",
                    str(self.workspace),
                    "--task-id",
                    "test-diagnostics-run",
                    "--test-target",
                    "tests.features.test_gauntlet",
                    "--diagnostics-json",
                ]
            )
        self.assertEqual(exit_code, 0)
        data = json.loads(stdout.getvalue())
        self.assertEqual(data["verdict"], "PASSED")
        self.assertIn("diagnostic_reports", data)
        self.assertIn("handoff_prompt", data)
        self.assertIn("CONTEXT.md", data["handoff_prompt"])

    def test_verify_includes_session_handoff_prompt(self) -> None:
        """Scenario CLI-06: Passing verify prints a clean Session Handoff prompt block."""
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "verify",
                    "-w",
                    str(self.workspace),
                    "--task-id",
                    "008-session-handoff-prompt-generator",
                    "--test-target",
                    "tests.features.test_gauntlet",
                ]
            )
        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("SESSION HANDOFF", output.upper())
        self.assertIn("CONTEXT.md", output)


    def test_init_with_harness(self) -> None:
        """Scenario CLI-INIT-HARNESS: init accepts --harness and records it in ScaffoldResult."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["init", "-w", tmpdir, "--harness", "antigravity", "--json"])
            self.assertEqual(exit_code, 0)
            data = json.loads(stdout.getvalue())
            self.assertEqual(data["harness"], "antigravity")

    def test_validate_plugin_command_valid(self) -> None:
        """Scenario CLI-PLUGIN-VALID: validate-plugin returns 0 for repo's plugin."""
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main([
                "validate-plugin",
                "-w",
                str(self.workspace),
                "--plugin-dir",
                "plugins/agent-gauntlet",
                "--harness",
                "antigravity",
            ])
        self.assertEqual(exit_code, 0)
        self.assertIn("VALID", stdout.getvalue().upper())

    def test_validate_plugin_command_json(self) -> None:
        """Scenario CLI-PLUGIN-JSON: validate-plugin --json outputs valid JSON."""
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main([
                "validate-plugin",
                "-w",
                str(self.workspace),
                "--plugin-dir",
                "plugins/agent-gauntlet",
                "--json",
            ])
        self.assertEqual(exit_code, 0)
        data = json.loads(stdout.getvalue())
        self.assertTrue(data["valid"])
        self.assertEqual(data["harness"], "antigravity")

    def test_validate_plugin_command_invalid(self) -> None:
        """Scenario CLI-PLUGIN-INVALID: validate-plugin fails for broken directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main([
                    "validate-plugin",
                    "-w",
                    str(self.workspace),
                    "--plugin-dir",
                    tmpdir,
                ])
            self.assertEqual(exit_code, 1)
            self.assertIn("INVALID", stdout.getvalue().upper())


    def test_okf_validate_command(self) -> None:
        """Scenario CLI-OKF-VALIDATE: okf validate returns 0 for workspace documentation."""
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["okf", "validate", "-w", str(self.workspace)])
        self.assertEqual(exit_code, 0)
        self.assertIn("VALID", stdout.getvalue())

    def test_okf_validate_json(self) -> None:
        """Scenario CLI-OKF-JSON: okf validate --json outputs structured report."""
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["okf", "validate", "-w", str(self.workspace), "--json"])
        self.assertEqual(exit_code, 0)
        data = json.loads(stdout.getvalue())
        self.assertTrue(data["valid"])
        self.assertGreater(data["total_files"], 0)

    def test_okf_stamp_command(self) -> None:
        """Scenario CLI-OKF-STAMP: okf stamp updates frontmatter in target file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Test Document\nBody", encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main([
                    "okf",
                    "stamp",
                    str(test_file),
                    "-w",
                    tmpdir,
                    "--type",
                    "Task Package",
                    "--status",
                    "draft",
                    "--generated-by",
                    "antigravity/gemini-3.7-flash",
                ])
            self.assertEqual(exit_code, 0)
            self.assertIn("Stamped OKF", stdout.getvalue())
            content = test_file.read_text(encoding="utf-8")
            self.assertIn("type: Task Package", content)
            self.assertIn("status: draft", content)


if __name__ == "__main__":
    unittest.main()


