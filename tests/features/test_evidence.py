"""Black-box acceptance tests for features/evidence (VerificationReportEngine & Schema v2)."""

import json
import unittest
from pathlib import Path

from agent_gauntlet.features.evidence import (
    CheckSummary,
    ExecutionMetadata,
    TaskContract,
    VerificationReport,
    VerificationReportEngine,
    WorkspaceState,
)


class TestVerificationReportEngine(unittest.TestCase):
    """Acceptance and invariant tests for VerificationReportEngine."""

    def setUp(self) -> None:
        self.engine = VerificationReportEngine()
        self.sample_report = VerificationReport(
            schema_version="2.0.0",
            execution_origin="LOCAL",
            verdict="PASSED",
            task_contract=TaskContract(
                task_id="016-cryptographic-cleanup",
                task_title="Cryptographic Cleanup & Unsigned Report Engine",
                task_digest="4c8996fb92427ae41e4649b934ca495991b7852b855e3b0c44298fc1c149afbf",
                acceptance_criteria=["Delete DEFAULT_KEY", "Implement Schema v2"],
                unresolved_criteria=[],
            ),
            workspace_state=WorkspaceState(
                manifest_version="1.0",
                source_content_digest="a1b2c3d4e5f60011a1b2c3d4e5f60011a1b2c3d4e5f60011a1b2c3d4e5f60011",
                source_manifest_digest_pre="7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
                source_manifest_digest_post="7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
                config_digest="4a5cb81e4a5cb81e4a5cb81e4a5cb81e4a5cb81e4a5cb81e4a5cb81e4a5cb81e",
                policy_digest="9d12c34a9d12c34a9d12c34a9d12c34a9d12c34a9d12c34a9d12c34a9d12c34a",
                check_definitions_digest="f1e2d3c4b5a60718f1e2d3c4b5a60718f1e2d3c4b5a60718f1e2d3c4b5a60718",
                included_files_count=48,
            ),
            execution_metadata=ExecutionMetadata(
                started_at="2026-08-25T15:27:37.100Z",
                finished_at="2026-08-25T15:27:49.250Z",
                total_duration_seconds=12.15,
                environment={
                    "python_version": "3.12.3",
                    "platform": "linux-x86_64",
                    "gauntlet_version": "0.2.0",
                },
            ),
            checks=[
                CheckSummary(
                    name="unit-tests", status="PASSED", exit_code=0, duration_seconds=0.12
                ),
                CheckSummary(
                    name="mutation-testing", status="PASSED", exit_code=0, duration_seconds=1.45
                ),
            ],
        )

    def test_zero_local_secrets_invariant(self) -> None:
        """Invariant: No DEFAULT_KEY, signing key, or HMAC fallback secret exists in source code."""
        src_root = Path(__file__).resolve().parent.parent.parent / "src"
        forbidden_tokens = [
            b"DEFAULT_KEY",
            b"agent-gauntlet-default-authority-key",
            b"secret_key",
        ]
        for py_file in src_root.rglob("*.py"):
            content = py_file.read_bytes()
            for token in forbidden_tokens:
                self.assertNotIn(
                    token,
                    content,
                    f"Forbidden secret token '{token.decode()}' found in {py_file}",
                )

    def test_report_json_roundtrip(self) -> None:
        """Scenario: Verification report serializes to Schema v2 JSON and deserializes cleanly."""
        json_str = self.engine.generate_report_json(self.sample_report)
        data = json.loads(json_str)

        self.assertEqual(data["schema_version"], "2.0.0")
        self.assertEqual(data["verdict"], "PASSED")
        self.assertEqual(data["execution_origin"], "LOCAL")
        self.assertNotIn("signature", data)

        loaded = self.engine.load_report_json(json_str)
        self.assertEqual(loaded.schema_version, "2.0.0")
        self.assertEqual(loaded.verdict, "PASSED")
        self.assertEqual(loaded.task_contract.task_id, "016-cryptographic-cleanup")
        self.assertEqual(
            loaded.workspace_state.source_manifest_digest_post,
            self.sample_report.workspace_state.source_manifest_digest_post,
        )
        self.assertEqual(len(loaded.checks), 2)
        self.assertEqual(loaded.checks[0].name, "unit-tests")

    def test_source_manifest_drift_detection(self) -> None:
        """Scenario: Verify matching source manifest passes and drifted manifest is detected."""
        matching_digest = "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
        drifted_digest = "0000000000000000000000000000000000000000000000000000000000000000"

        self.assertTrue(
            self.engine.verify_workspace_state_match(self.sample_report, matching_digest),
            "Matching manifest digest must pass state verification",
        )
        self.assertFalse(
            self.engine.verify_workspace_state_match(self.sample_report, drifted_digest),
            "Drifted manifest digest must fail state verification",
        )

    def test_markdown_report_generation(self) -> None:
        """Scenario: Markdown rendering includes task contract, checks table, and manifest digests."""
        md = self.engine.generate_report_markdown(
            self.sample_report, title="Local Verification Report"
        )

        self.assertIn("# Local Verification Report", md)
        self.assertIn("016-cryptographic-cleanup", md)
        self.assertIn("PASSED", md)
        self.assertIn("7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069", md)
        self.assertIn("unit-tests", md)
        self.assertIn("mutation-testing", md)
        self.assertIn("- [x] Delete DEFAULT_KEY", md)

    def test_empty_report_digest_fails_verification(self) -> None:
        """Scenario: Empty report digest returns False without crashing."""
        empty_report = VerificationReport(
            schema_version="2.0.0",
            execution_origin="LOCAL",
            verdict="PASSED",
            workspace_state=WorkspaceState(source_manifest_digest_post=""),
        )
        self.assertFalse(self.engine.verify_workspace_state_match(empty_report, "7f83b1657ff1fc53"))

    def test_load_report_json_preserves_failed_verdict(self) -> None:
        """Scenario: Loading a report with verdict FAILED preserves FAILED verdict."""
        failed_report = VerificationReport(
            schema_version="2.0.0",
            execution_origin="LOCAL",
            verdict="FAILED",
            workspace_state=WorkspaceState(source_manifest_digest_post="7f83b1657ff1fc53"),
        )
        json_str = self.engine.generate_report_json(failed_report)
        loaded = self.engine.load_report_json(json_str)
        self.assertEqual(loaded.verdict, "FAILED")

    def test_legacy_evidence_classification(self) -> None:
        """Scenario: Legacy v1 evidence.json with HMAC signature is classified as LEGACY_UNATTESTED."""
        legacy_json = json.dumps(
            {
                "task_id": "legacy-task-001",
                "status": "PASSED",
                "source_tree_hash": "a1b2c3d4e5f60011",
                "signature": "e9b5f...legacy-hmac",
                "checks": [{"name": "unit", "passed": True, "exit_code": 0}],
            }
        )
        classification = self.engine.classify_evidence_payload(legacy_json)
        self.assertEqual(classification, "LEGACY_UNATTESTED")


class TestRoleAwareHandoffEngine(unittest.TestCase):
    """Black-box acceptance tests for infer_next_session_role and role-aware handoffs."""

    def setUp(self) -> None:
        import tempfile

        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.tasks_dir = self.workspace / "tasks"
        self.tasks_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_infer_role_when_next_task_is_draft(self) -> None:
        """Scenario: Next task is DRAFT -> Returns Senior Software Engineer (System Architecture & Requirements)."""
        from agent_gauntlet.features.evidence.verifier import infer_next_session_role

        (self.tasks_dir / "001-completed.md").write_text(
            "# Task 001\n**Status**: `DONE`\n- [x] Done", encoding="utf-8"
        )
        (self.tasks_dir / "002-new-idea.md").write_text(
            "# Task 002\n**Status**: `DRAFT`\n## 🎯 Formål\nNoget nyt", encoding="utf-8"
        )

        next_role, next_task_id, prompt = infer_next_session_role(self.workspace, "001-completed")

        self.assertEqual(next_role, "Senior Software Engineer (System Architecture & Requirements)")
        self.assertEqual(next_task_id, "002-new-idea")
        self.assertIn("System Architecture & Requirements", prompt)
        self.assertIn("tasks/002-new-idea.md", prompt)
        self.assertIn("spec.md", prompt)
        self.assertNotIn("old-coder", prompt.lower())

    def test_infer_role_when_next_task_is_active(self) -> None:
        """Scenario: Next task is ACTIVE with [ ] -> Returns Senior Software Engineer (Feature Implementation & Testing)."""
        from agent_gauntlet.features.evidence.verifier import infer_next_session_role

        (self.tasks_dir / "001-completed.md").write_text(
            "# Task 001\n**Status**: `DONE`\n- [x] Done", encoding="utf-8"
        )
        (self.tasks_dir / "002-feature.md").write_text(
            "# Task 002\n**Status**: `ACTIVE`\n- [ ] Implement feature\n- [ ] Add tests",
            encoding="utf-8",
        )

        next_role, next_task_id, prompt = infer_next_session_role(self.workspace, "001-completed")

        self.assertEqual(next_role, "Senior Software Engineer (Feature Implementation & Testing)")
        self.assertEqual(next_task_id, "002-feature")
        self.assertIn("Feature Implementation & Testing", prompt)
        self.assertIn("tasks/002-feature.md", prompt)
        self.assertIn("Test-Driven Development", prompt)
        self.assertNotIn("old-coder", prompt.lower())

    def test_infer_role_when_all_tasks_are_done(self) -> None:
        """Scenario: All feature tasks are DONE (pre-audit) -> Returns Senior Software Engineer (Independent Code Review & Audit)."""
        from agent_gauntlet.features.evidence.verifier import infer_next_session_role

        (self.tasks_dir / "001-first.md").write_text(
            "# Task 001\n**Status**: `DONE`\n- [x] Done", encoding="utf-8"
        )
        (self.tasks_dir / "002-second.md").write_text(
            "# Task 002\n**Status**: `DONE`\n- [x] Done", encoding="utf-8"
        )

        next_role, next_task_id, prompt = infer_next_session_role(self.workspace, "002-second")

        self.assertEqual(next_role, "Senior Software Engineer (Independent Code Review & Audit)")
        self.assertEqual(next_task_id, "")
        self.assertIn("Independent Code Review & Audit", prompt)
        self.assertIn("code-review", prompt.lower())
        self.assertNotIn("old-coder", prompt.lower())

    def test_infer_role_when_audit_task_is_completed(self) -> None:
        """Scenario: Audit/review task is completed -> Returns Release & Operations Engineer (Release Attestation & Deployment)."""
        from agent_gauntlet.features.evidence.verifier import infer_next_session_role

        (self.tasks_dir / "001-feature.md").write_text(
            "# Task 001\n**Status**: `DONE`\n- [x] Feature done", encoding="utf-8"
        )
        (self.tasks_dir / "002-code-review-audit.md").write_text(
            "# Task 002: Code Review Audit\n**Status**: `DONE`\n- [x] Audit remediated",
            encoding="utf-8",
        )

        next_role, next_task_id, prompt = infer_next_session_role(
            self.workspace, "002-code-review-audit"
        )

        self.assertEqual(
            next_role, "Release & Operations Engineer (Release Attestation & Deployment)"
        )
        self.assertEqual(next_task_id, "")
        self.assertIn("Release & Operations Engineer", prompt)
        self.assertIn("check-attestation", prompt)
        self.assertIn("ROADMAP.md", prompt)

    def test_infer_role_when_current_task_is_audit_remediation(self) -> None:
        """Scenario: current_task_id is an audit remediation task and all tasks are DONE -> Returns Release role."""
        from agent_gauntlet.features.evidence.verifier import infer_next_session_role

        (self.tasks_dir / "028-code-review-audit-remediation.md").write_text(
            "# Task 028: Code Review Remediation\n**Status**: `DONE`\n- [x] All done",
            encoding="utf-8",
        )

        next_role, next_task_id, prompt = infer_next_session_role(
            self.workspace, "028-code-review-audit-remediation"
        )

        self.assertEqual(
            next_role, "Release & Operations Engineer (Release Attestation & Deployment)"
        )
        self.assertEqual(next_task_id, "")
        self.assertIn("Release & Operations Engineer", prompt)


if __name__ == "__main__":
    unittest.main()
