"""Black-box acceptance tests for agent_gauntlet.cli."""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_gauntlet.cli import main
from agent_gauntlet.features.evidence import (
    CheckSummary,
    TaskContract,
    VerificationReport,
    VerificationReportEngine,
    WorkspaceState,
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
                exit_code = main(
                    ["init", "-w", tmpdir, "--stack", "typescript", "--format", "json"]
                )
            self.assertEqual(exit_code, 0)
            created_file = Path(tmpdir) / "gauntlet.json"
            self.assertTrue(created_file.exists())
            self.assertIn('"stack": "typescript"', created_file.read_text())

    def test_tree_hash_command(self) -> None:
        """Scenario CLI-01: tree-hash prints tree hash and returns 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "file.txt").write_text("hello", encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["tree-hash", "-w", str(ws)])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue().strip()
            self.assertGreaterEqual(len(output), 16)
            _, _, expected_tree = compute_source_state(ws)
            self.assertEqual(output, expected_tree)

    def test_check_evidence_valid(self) -> None:
        """Scenario CLI-02: check-evidence verifies valid unsigned verification report matching manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "file.txt").write_text("hello", encoding="utf-8")
            from agent_gauntlet.features.evidence import compute_workspace_manifest

            manifest = compute_workspace_manifest(ws)
            engine = VerificationReportEngine()
            report = VerificationReport(
                schema_version="2.0.0",
                execution_origin="LOCAL",
                verdict="PASSED",
                task_contract=TaskContract(task_id="task-cli-valid", acceptance_criteria=[]),
                workspace_state=WorkspaceState(
                    source_manifest_digest_post=manifest.source_manifest_digest,
                    source_content_digest=manifest.source_content_digest,
                ),
                checks=[CheckSummary(name="unit-tests", status="PASSED", passed=True, exit_code=0)],
            )
            report_file = ws / "verification-report.json"
            report_file.write_text(engine.generate_report_json(report), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    ["check-evidence", "-w", str(ws), "--evidence-file", str(report_file)]
                )
            self.assertEqual(exit_code, 0)
            self.assertIn("VALID", stdout.getvalue().upper())
            self.assertIn("LOCAL", stdout.getvalue().upper())

    def test_check_evidence_legacy_fails_by_default(self) -> None:
        """Scenario CLI-03a: check-evidence rejects legacy v1 HMAC evidence by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "file.txt").write_text("hello", encoding="utf-8")
            _, _, current_tree = compute_source_state(ws)
            legacy_data = {
                "task_id": "task-legacy",
                "status": "PASSED",
                "source_tree_hash": current_tree,
                "signature": "old-hmac-signature-abcdef",
                "checks": [{"name": "unit", "passed": True, "exit_code": 0}],
            }
            temp_path = ws / "evidence.json"
            temp_path.write_text(json.dumps(legacy_data), encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    ["check-evidence", "-w", str(ws), "--evidence-file", str(temp_path)]
                )
            self.assertEqual(exit_code, 1)
            self.assertIn("legacy v1 hmac evidence detected", stderr.getvalue().lower())

    def test_check_evidence_legacy_advisory_mode(self) -> None:
        """Scenario CLI-03b: check-evidence accepts legacy v1 HMAC evidence when --legacy-advisory is set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "file.txt").write_text("hello", encoding="utf-8")
            _, _, current_tree = compute_source_state(ws)
            legacy_data = {
                "task_id": "task-legacy",
                "status": "PASSED",
                "source_tree_hash": current_tree,
                "signature": "old-hmac-signature-abcdef",
                "checks": [{"name": "unit", "passed": True, "exit_code": 0}],
            }
            temp_path = ws / "evidence.json"
            temp_path.write_text(json.dumps(legacy_data), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "check-evidence",
                        "-w",
                        str(ws),
                        "--evidence-file",
                        str(temp_path),
                        "--legacy-advisory",
                    ]
                )
            self.assertEqual(exit_code, 0)
            self.assertIn("LEGACY_UNATTESTED", stdout.getvalue())

    def test_check_evidence_drifted_fails(self) -> None:
        """Scenario CLI-03c: check-evidence fails on mismatched manifest digest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "file.txt").write_text("hello", encoding="utf-8")
            engine = VerificationReportEngine()
            report = VerificationReport(
                schema_version="2.0.0",
                execution_origin="LOCAL",
                verdict="PASSED",
                task_contract=TaskContract(task_id="task-cli-drifted"),
                workspace_state=WorkspaceState(
                    source_manifest_digest_post="deadbeef00000000",
                ),
                checks=[CheckSummary(name="unit-tests", status="PASSED", passed=True, exit_code=0)],
            )
            temp_path = ws / "verification-report.json"
            temp_path.write_text(engine.generate_report_json(report), encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    ["check-evidence", "-w", str(ws), "--evidence-file", str(temp_path)]
                )
            self.assertEqual(exit_code, 1)
            self.assertIn("drift detected", stderr.getvalue().lower())

    def test_verify_command_pass(self) -> None:
        """Scenario CLI-04: verify runs layers in isolated workspace and returns 0 on success."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            main(["init", "-w", str(ws), "--harness", "antigravity"])
            tests_dir = ws / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "test_sample.py").write_text(
                "import unittest\nclass TestS(unittest.TestCase):\n    def test_ok(self): pass\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "verify",
                        "-w",
                        str(ws),
                        "--task-id",
                        "test-verify-run",
                        "--test-target",
                        "tests.test_sample",
                    ]
                )
            self.assertEqual(exit_code, 0)
            self.assertIn("PARTIAL", stdout.getvalue().upper())

    def test_verify_diagnostics_json(self) -> None:
        """Scenario CLI-05: verify with --diagnostics-json outputs structured json in isolated workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            main(["init", "-w", str(ws), "--harness", "antigravity"])
            tests_dir = ws / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "test_sample.py").write_text(
                "import unittest\nclass TestS(unittest.TestCase):\n    def test_ok(self): pass\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "verify",
                        "-w",
                        str(ws),
                        "--task-id",
                        "test-diagnostics-run",
                        "--test-target",
                        "tests.test_sample",
                        "--diagnostics-json",
                    ]
                )
            self.assertEqual(exit_code, 0)
            data = json.loads(stdout.getvalue())
            self.assertEqual(data["verdict"], "PARTIAL")
            self.assertIn("diagnostic_reports", data)

    def test_verify_includes_session_handoff_prompt(self) -> None:
        """Scenario CLI-06: Full passing verify prints a clean Session Handoff prompt block."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            main(["init", "-w", str(ws), "--harness", "antigravity"])
            # Create a task with all criteria marked resolved
            task_file = ws / "tasks/001-done-task.md"
            task_file.write_text(
                "---\n"
                "type: Task Package\n"
                "title: Done Task\n"
                "description: Done task description\n"
                "status: draft\n"
                "tags: [test]\n"
                "generated: { by: antigravity/gemini-3.7-flash, at: '2026-08-25T15:00:00Z' }\n"
                "---\n"
                "# Task 001: Done Task\n- [x] All resolved\n",
                encoding="utf-8",
            )
            tests_dir = ws / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "test_sample.py").write_text(
                "import unittest\nclass TestS(unittest.TestCase):\n    def test_ok(self): pass\n",
                encoding="utf-8",
            )
            (ws / "gauntlet.toml").write_text(
                f'stack = "python"\n[[layers]]\nname = "unit"\ncommand = ["{sys.executable}", "-m", "unittest", "discover", "tests"]\noptional = false\n',
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "verify",
                        "-w",
                        str(ws),
                        "--task-id",
                        "001-done-task",
                    ]
                )
            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("SESSION HANDOFF", output.upper())
            self.assertIn("CONTEXT.md", output)

    def test_verify_saves_unsigned_report_and_preserves_task_files(self) -> None:
        """Scenario CLI-07: verify writes unsigned verification-report.json and does not mutate task files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Scaffold workspace in tmp
            main(["init", "-w", str(tmp_path), "--harness", "antigravity"])
            # Create sample task
            tasks_dir = tmp_path / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)
            task_file = tasks_dir / "001-sample-task.md"
            initial_task_content = (
                "---\n"
                "type: Task Package\n"
                "title: Sample Task\n"
                "description: Sample task description\n"
                "status: draft\n"
                "tags: [test]\n"
                "generated: { by: antigravity/gemini-3.7-flash, at: '2026-08-25T15:00:00Z' }\n"
                "---\n"
                "# Task 001: Sample Task\n- [x] Criterion 1\n"
            )
            task_file.write_text(initial_task_content, encoding="utf-8")

            # Create passing test file
            tests_dir = tmp_path / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "__init__.py").write_text("", encoding="utf-8")
            (tests_dir / "test_sample.py").write_text(
                "import unittest\nclass TestSample(unittest.TestCase):\n    def test_ok(self): pass\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "verify",
                        "-w",
                        str(tmp_path),
                        "--task-id",
                        "001-sample-task",
                        "--test-target",
                        "tests.test_sample",
                    ]
                )
            self.assertEqual(exit_code, 0)

            # Assert verification-report.json was created and is unsigned Schema v2
            report_file = tmp_path / "verification-report.json"
            self.assertTrue(report_file.is_file(), "verification-report.json must be created")
            data = json.loads(report_file.read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], "2.0.0")
            self.assertEqual(data["execution_origin"], "LOCAL")
            self.assertNotIn("signature", data)

            # Assert zero self-mutation: task file content remains unchanged
            final_task_content = task_file.read_text(encoding="utf-8")
            self.assertEqual(
                final_task_content,
                initial_task_content,
                "verify must not mutate task markdown files (zero self-mutation invariant)",
            )

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
            exit_code = main(
                [
                    "validate-plugin",
                    "-w",
                    str(self.workspace),
                    "--plugin-dir",
                    "plugins/agent-gauntlet",
                    "--harness",
                    "antigravity",
                ]
            )
        self.assertEqual(exit_code, 0)
        self.assertIn("VALID", stdout.getvalue().upper())

    def test_validate_plugin_command_json(self) -> None:
        """Scenario CLI-PLUGIN-JSON: validate-plugin --json outputs valid JSON."""
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "validate-plugin",
                    "-w",
                    str(self.workspace),
                    "--plugin-dir",
                    "plugins/agent-gauntlet",
                    "--json",
                ]
            )
        self.assertEqual(exit_code, 0)
        data = json.loads(stdout.getvalue())
        self.assertTrue(data["valid"])
        self.assertEqual(data["harness"], "antigravity")

    def test_validate_plugin_command_invalid(self) -> None:
        """Scenario CLI-PLUGIN-INVALID: validate-plugin fails for broken directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "validate-plugin",
                        "-w",
                        str(self.workspace),
                        "--plugin-dir",
                        tmpdir,
                    ]
                )
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
                exit_code = main(
                    [
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
                    ]
                )
            self.assertEqual(exit_code, 0)
            self.assertIn("Stamped OKF", stdout.getvalue())
            content = test_file.read_text(encoding="utf-8")
            self.assertIn("type: Task Package", content)
            self.assertIn("status: draft", content)

    def test_check_attestation_valid_bundle_passes(self) -> None:
        """Scenario CLI-ATTEST-01: check-attestation with valid report and bundle returns 0."""
        from agent_gauntlet.features.evidence import compute_workspace_manifest
        from agent_gauntlet.features.evidence.attestation import AttestationEngine

        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "tasks").mkdir()
            (ws / "tasks/001-init.md").write_text("# Task\n- [x] done\n")
            manifest = compute_workspace_manifest(ws)

            engine = VerificationReportEngine()
            att_engine = AttestationEngine()
            report = VerificationReport(
                schema_version="2.0.0",
                execution_origin="CI_PROTECTED",
                verdict="PASSED",
                task_contract=TaskContract(task_id="001-init", acceptance_criteria=["done"]),
                workspace_state=WorkspaceState(
                    source_manifest_digest_post=manifest.source_manifest_digest
                ),
            )
            report_str = engine.generate_report_json(report)
            (ws / "verification-report.json").write_text(report_str, encoding="utf-8")
            subject_digest = att_engine.compute_report_subject_digest(report_str)

            bundle_data = {
                "bundle_version": "0.1",
                "status": "VALID",
                "identity": {
                    "issuer": "https://token.actions.githubusercontent.com",
                    "repository": "rolfmadsen/agent-gauntlet",
                    "workflow": ".github/workflows/ci.yml@refs/heads/main",
                },
                "subject_digest": subject_digest,
            }
            (ws / "attestation.json").write_text(json.dumps(bundle_data), encoding="utf-8")

            policy_data = {
                "policy_version": "1.0",
                "require_attestation": True,
                "allowed_oidc_issuers": ["https://token.actions.githubusercontent.com"],
                "allowed_repositories": ["rolfmadsen/agent-gauntlet"],
            }
            (ws / "trust-policy.json").write_text(json.dumps(policy_data), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "check-attestation",
                        "-w",
                        str(ws),
                        "-r",
                        str(ws / "verification-report.json"),
                        "-a",
                        str(ws / "attestation.json"),
                        "-p",
                        str(ws / "trust-policy.json"),
                        "--json",
                    ]
                )
            self.assertEqual(exit_code, 0)
            res = json.loads(stdout.getvalue())
            self.assertEqual(res["verification_result"], "PASSED")
            self.assertEqual(res["attestation_status"], "VALID")
            self.assertEqual(res["trust_decision"], "ACCEPTED")
            self.assertTrue(res["release_eligible"])

    def test_check_attestation_signed_failure_is_trusted_but_release_rejected(self) -> None:
        """Scenario CLI-ATTEST-02: Signed failure has VALID attestation but exit code 1."""
        from agent_gauntlet.features.evidence import compute_workspace_manifest
        from agent_gauntlet.features.evidence.attestation import AttestationEngine

        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            manifest = compute_workspace_manifest(ws)

            engine = VerificationReportEngine()
            att_engine = AttestationEngine()
            report = VerificationReport(
                schema_version="2.0.0",
                execution_origin="CI_PROTECTED",
                verdict="FAILED",
                task_contract=TaskContract(task_id="001-init"),
                workspace_state=WorkspaceState(
                    source_manifest_digest_post=manifest.source_manifest_digest
                ),
            )
            report_str = engine.generate_report_json(report)
            (ws / "verification-report.json").write_text(report_str, encoding="utf-8")
            subject_digest = att_engine.compute_report_subject_digest(report_str)

            bundle_data = {
                "bundle_version": "0.1",
                "status": "VALID",
                "identity": {
                    "issuer": "https://token.actions.githubusercontent.com",
                    "repository": "rolfmadsen/agent-gauntlet",
                },
                "subject_digest": subject_digest,
            }
            (ws / "attestation.json").write_text(json.dumps(bundle_data), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "check-attestation",
                        "-w",
                        str(ws),
                        "-r",
                        str(ws / "verification-report.json"),
                        "-a",
                        str(ws / "attestation.json"),
                        "--json",
                    ]
                )
            self.assertEqual(exit_code, 1, "Failed verdict must reject release eligibility")
            res = json.loads(stdout.getvalue())
            self.assertEqual(res["verification_result"], "FAILED")
            self.assertEqual(res["attestation_status"], "VALID")
            self.assertEqual(res["trust_decision"], "ACCEPTED")
            self.assertFalse(res["release_eligible"])

    def test_check_attestation_manifest_drift_fails(self) -> None:
        """Scenario CLI-ATTEST-03: Manifest drift fails check-attestation even with --allow-unattested."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            engine = VerificationReportEngine()
            report = VerificationReport(
                schema_version="2.0.0",
                execution_origin="LOCAL",
                verdict="PASSED",
                task_contract=TaskContract(task_id="001-init"),
                workspace_state=WorkspaceState(
                    source_manifest_digest_post="drifted_digest_1234567890abcdef1234567890abcdef"
                ),
            )
            report_str = engine.generate_report_json(report)
            (ws / "verification-report.json").write_text(report_str, encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        "check-attestation",
                        "-w",
                        str(ws),
                        "-r",
                        str(ws / "verification-report.json"),
                        "--allow-unattested",
                    ]
                )
            self.assertEqual(
                exit_code, 1, "Drift must fail check-attestation even when unattested is allowed"
            )
            self.assertIn("drift", stderr.getvalue().lower())

    def test_check_attestation_absent_attestation_fails_without_allow_flag(self) -> None:
        """Scenario CLI-ATTEST-04: Absent attestation on PASSED verdict fails without --allow-unattested."""
        from agent_gauntlet.features.evidence import compute_workspace_manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            manifest = compute_workspace_manifest(ws)

            engine = VerificationReportEngine()
            report = VerificationReport(
                schema_version="2.0.0",
                execution_origin="LOCAL",
                verdict="PASSED",
                task_contract=TaskContract(task_id="001-init"),
                workspace_state=WorkspaceState(
                    source_manifest_digest_post=manifest.source_manifest_digest
                ),
            )
            report_str = engine.generate_report_json(report)
            (ws / "verification-report.json").write_text(report_str, encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "check-attestation",
                        "-w",
                        str(ws),
                        "-r",
                        str(ws / "verification-report.json"),
                        "--json",
                    ]
                )
            self.assertEqual(exit_code, 1, "Must fail closed when attestation is absent")
            res = json.loads(stdout.getvalue())
            self.assertEqual(res["attestation_status"], "ABSENT")
            self.assertFalse(res["release_eligible"])

    def test_check_attestation_allow_unattested_fails_on_failed_verdict(self) -> None:
        """Scenario CLI-ATTEST-05: allow-unattested on FAILED verdict returns exit code 1."""
        from agent_gauntlet.features.evidence import compute_workspace_manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            manifest = compute_workspace_manifest(ws)

            engine = VerificationReportEngine()
            report = VerificationReport(
                schema_version="2.0.0",
                execution_origin="LOCAL",
                verdict="FAILED",
                task_contract=TaskContract(task_id="001-init"),
                workspace_state=WorkspaceState(
                    source_manifest_digest_post=manifest.source_manifest_digest
                ),
            )
            report_str = engine.generate_report_json(report)
            (ws / "verification-report.json").write_text(report_str, encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "check-attestation",
                        "-w",
                        str(ws),
                        "-r",
                        str(ws / "verification-report.json"),
                        "--allow-unattested",
                        "--json",
                    ]
                )
            self.assertEqual(exit_code, 1)
            res = json.loads(stdout.getvalue())
            self.assertEqual(res["verification_result"], "FAILED")
            self.assertFalse(res["release_eligible"])

    def test_verify_targeted_test_has_partial_verdict(self) -> None:
        """Scenario CLI-08: verify with --test-target produces PARTIAL verdict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            main(["init", "-w", str(ws), "--harness", "antigravity"])
            tests_dir = ws / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "test_dummy.py").write_text(
                "import unittest\nclass TestD(unittest.TestCase):\n    def test_one(self): pass\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "verify",
                        "-w",
                        str(ws),
                        "--task-id",
                        "001-bootstrap",
                        "--test-target",
                        "tests.test_dummy",
                        "--json",
                    ]
                )
            self.assertEqual(exit_code, 0)
            data = json.loads(stdout.getvalue())
            self.assertEqual(data["verdict"], "PARTIAL")

    def test_verify_unresolved_criteria_yields_incomplete_verdict_and_fails_exit_code(self) -> None:
        """Scenario CLI-09: verify with unresolved acceptance criteria produces INCOMPLETE verdict and exit code 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            main(["init", "-w", str(ws), "--harness", "antigravity"])
            # Create a task with an unresolved criterion
            task_file = ws / "tasks/001-open-task.md"
            task_file.write_text(
                "---\n"
                "type: Task Package\n"
                "title: Open Task\n"
                "description: Open task description\n"
                "status: draft\n"
                "tags: [test]\n"
                "generated: { by: antigravity/gemini-3.7-flash, at: '2026-08-25T15:00:00Z' }\n"
                "---\n"
                "# Task 001: Open Task\n- [ ] Unfinished Criterion\n",
                encoding="utf-8",
            )
            tests_dir = ws / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "test_sample.py").write_text(
                "import unittest\nclass TestS(unittest.TestCase):\n    def test_ok(self): pass\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "verify",
                        "-w",
                        str(ws),
                        "--task-id",
                        "001-open-task",
                        "--json",
                    ]
                )
            self.assertEqual(
                exit_code, 1, "Unresolved criteria must cause verify to fail with exit code 1"
            )
            data = json.loads(stdout.getvalue())
            self.assertEqual(data["verdict"], "INCOMPLETE")

    def test_check_evidence_rejects_partial_verdict(self) -> None:
        """Scenario CLI-10: check-evidence rejects report with PARTIAL verdict."""
        from agent_gauntlet.features.evidence import compute_workspace_manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            manifest = compute_workspace_manifest(ws)
            engine = VerificationReportEngine()
            report = VerificationReport(
                schema_version="2.0.0",
                execution_origin="LOCAL",
                verdict="PARTIAL",
                task_contract=TaskContract(task_id="001-partial"),
                workspace_state=WorkspaceState(
                    source_manifest_digest_post=manifest.source_manifest_digest
                ),
                checks=[CheckSummary(name="test", status="PASSED", passed=True, exit_code=0)],
            )
            report_file = ws / "verification-report.json"
            report_file.write_text(engine.generate_report_json(report), encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    ["check-evidence", "-w", str(ws), "--evidence-file", str(report_file)]
                )
            self.assertEqual(exit_code, 1)
            self.assertIn("non-passed verdict", stderr.getvalue().lower())

    def test_check_evidence_rejects_failed_checks(self) -> None:
        """Scenario CLI-11: check-evidence rejects report containing failed checks despite PASSED verdict."""
        from agent_gauntlet.features.evidence import compute_workspace_manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            manifest = compute_workspace_manifest(ws)
            engine = VerificationReportEngine()
            report = VerificationReport(
                schema_version="2.0.0",
                execution_origin="LOCAL",
                verdict="PASSED",
                task_contract=TaskContract(task_id="001-fake-pass"),
                workspace_state=WorkspaceState(
                    source_manifest_digest_post=manifest.source_manifest_digest
                ),
                checks=[
                    CheckSummary(name="unit-tests", status="FAILED", passed=False, exit_code=1)
                ],
            )
            report_file = ws / "verification-report.json"
            report_file.write_text(engine.generate_report_json(report), encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    ["check-evidence", "-w", str(ws), "--evidence-file", str(report_file)]
                )
            self.assertEqual(exit_code, 1)
            self.assertIn("failed check", stderr.getvalue().lower())

    def test_check_evidence_rejects_unresolved_criteria(self) -> None:
        """Scenario CLI-12: check-evidence rejects report with unresolved acceptance criteria."""
        from agent_gauntlet.features.evidence import compute_workspace_manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            manifest = compute_workspace_manifest(ws)
            engine = VerificationReportEngine()
            report = VerificationReport(
                schema_version="2.0.0",
                execution_origin="LOCAL",
                verdict="PASSED",
                task_contract=TaskContract(
                    task_id="001-open",
                    acceptance_criteria=["Criterion 1"],
                    unresolved_criteria=["Criterion 1"],
                ),
                workspace_state=WorkspaceState(
                    source_manifest_digest_post=manifest.source_manifest_digest
                ),
                checks=[CheckSummary(name="test", status="PASSED", passed=True, exit_code=0)],
            )
            report_file = ws / "verification-report.json"
            report_file.write_text(engine.generate_report_json(report), encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    ["check-evidence", "-w", str(ws), "--evidence-file", str(report_file)]
                )
            self.assertEqual(exit_code, 1)
            self.assertIn("unresolved acceptance criteria", stderr.getvalue().lower())

    def test_check_evidence_rejects_non_existent_file(self) -> None:
        """Scenario CLI-13: check-evidence returns exit 1 if evidence file does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    ["check-evidence", "-w", str(ws), "--evidence-file", "nonexistent.json"]
                )
            self.assertEqual(exit_code, 1)
            self.assertIn("does not exist", stderr.getvalue().lower())

    def test_check_evidence_rejects_corrupted_json(self) -> None:
        """Scenario CLI-14: check-evidence returns exit 1 on invalid/corrupted json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            bad_file = ws / "bad.json"
            bad_file.write_text("not json content", encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    ["check-evidence", "-w", str(ws), "--evidence-file", str(bad_file)]
                )
            self.assertEqual(exit_code, 1)
            self.assertIn("failed to parse", stderr.getvalue().lower())

    def test_verify_fails_when_workspace_is_self_mutated(self) -> None:
        """Scenario CLI-15: verify fails with FAILED verdict if test execution modifies source workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            main(["init", "-w", str(ws), "--harness", "antigravity"])
            # Create a task
            task_file = ws / "tasks/001-mutation.md"
            task_file.write_text(
                "---\ntype: Task Package\ntitle: Mut\ndescription: d\nstatus: draft\ntags: [t]\n"
                "generated: { by: antigravity/gemini-3.7-flash, at: '2026-08-25T15:00:00Z' }\n---\n"
                "# Task 001\n- [x] Done\n",
                encoding="utf-8",
            )
            # Create a test script that mutates src/ during run
            (ws / "tests").mkdir(parents=True, exist_ok=True)
            (ws / "tests" / "test_mutator.py").write_text(
                f"import unittest, pathlib\n"
                f"class TestM(unittest.TestCase):\n"
                f"    def test_mutate(self):\n"
                f"        (pathlib.Path('{ws}') / 'src' / 'leaked.py').write_text('exploit')\n",
                encoding="utf-8",
            )
            (ws / "gauntlet.toml").write_text(
                f'stack = "python"\n[[layers]]\nname = "unit"\ncommand = ["{sys.executable}", "-m", "unittest", "discover", "tests"]\noptional = false\n',
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["verify", "-w", str(ws), "--task-id", "001-mutation", "--json"])
            data = json.loads(stdout.getvalue())
            self.assertEqual(data["verdict"], "FAILED")

    def test_verify_marks_partial_on_optional_layer_failure(self) -> None:
        """Scenario CLI-16: verify marks run as PARTIAL if an optional layer fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            main(["init", "-w", str(ws), "--harness", "antigravity"])
            task_file = ws / "tasks/001-opt.md"
            task_file.write_text(
                "---\ntype: Task Package\ntitle: Opt\ndescription: d\nstatus: draft\ntags: [t]\n"
                "generated: { by: antigravity/gemini-3.7-flash, at: '2026-08-25T15:00:00Z' }\n---\n"
                "# Task 001\n- [x] Done\n",
                encoding="utf-8",
            )
            (ws / "tests").mkdir(parents=True, exist_ok=True)
            (ws / "tests" / "test_sample.py").write_text(
                "import unittest\nclass TestS(unittest.TestCase):\n    def test_ok(self): pass\n",
                encoding="utf-8",
            )
            (ws / "gauntlet.toml").write_text(
                f'stack = "python"\n'
                f'[[layers]]\nname = "unit"\ncommand = ["{sys.executable}", "-m", "unittest", "discover", "tests"]\noptional = false\n'
                f'[[layers]]\nname = "opt_layer"\ncommand = ["{sys.executable}", "-c", "import sys; sys.exit(9)"]\noptional = true\n',
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["verify", "-w", str(ws), "--task-id", "001-opt", "--json"])
            data = json.loads(stdout.getvalue())
            self.assertEqual(data["verdict"], "PARTIAL")


if __name__ == "__main__":
    unittest.main()
