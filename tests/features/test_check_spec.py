"""Acceptance and unit tests for Task 039: Early-Phase Specification and Business Rules Gatekeeper."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.cli import main
from agent_gauntlet.features.hooks.gatekeeper import PolicyEngine
from agent_gauntlet.features.hooks.models import (
    FileWriteRequest,
    GatekeeperVerdict,
    TrustedEnforcementContext,
)
from agent_gauntlet.features.tasks.spec_gate import (
    SpecReadinessReport,
    check_task_specification,
    validate_context_glossary,
)


class TestCheckSpecGatekeeper(unittest.TestCase):
    """Verifies that early-phase specifications and business rules are mechanically enforced."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.tasks_dir = self.workspace / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.src_dir = self.workspace / "src"
        self.src_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _setup_valid_context(self) -> None:
        context_content = (
            "---\n"
            "type: Knowledge Bundle Index\n"
            "title: Context Glossary\n"
            "status: stable\n"
            "generated: { by: test, at: '2026-08-30T09:00:00Z' }\n"
            "---\n\n"
            "# Context Glossary\n\n"
            "**Task**:\n"
            "An executable unit of engineering work, that has bounded acceptance criteria.\n"
            "_Avoid_: Ticket, issue, story.\n\n"
            "**Gatekeeper**:\n"
            "A shift-left policy engine, that evaluates specification readiness.\n"
            "_Avoid_: Linter, checker.\n"
        )
        (self.workspace / "CONTEXT.md").write_text(context_content, encoding="utf-8")

    def _create_task(
        self,
        task_id: str = "001-test-task",
        status: str = "active",
        with_must_not: bool = True,
        with_criteria: bool = True,
        with_purpose: bool = True,
    ) -> Path:
        must_not_section = (
            "## 🚫 Must NOT\n- Må IKKE overskride systemets tillidsgrænser.\n"
            if with_must_not
            else ""
        )
        criteria_section = (
            "## 📋 Acceptance Criteria\n- [ ] Opgaven skal verificeres via en red test.\n"
            if with_criteria
            else ""
        )
        purpose_section = (
            "## 🎯 Formål\nFormålet er at teste gatekeeperen.\n" if with_purpose else ""
        )

        content = (
            "---\n"
            "type: Task Package\n"
            f"title: 'Task: {task_id}'\n"
            f"status: {status}\n"
            "generated: { by: test, at: '2026-08-30T09:00:00Z' }\n"
            "---\n\n"
            f"# Task: {task_id}\n\n"
            f"**Status**: `{status.upper()}`\n\n"
            f"{purpose_section}\n"
            f"{criteria_section}\n"
            f"{must_not_section}\n"
            "## 🧪 Verifikation\n- `python3 -m unittest`\n"
        )
        task_path = self.tasks_dir / f"{task_id}.md"
        task_path.write_text(content, encoding="utf-8")
        return task_path

    def test_valid_task_specification_passes(self) -> None:
        self._setup_valid_context()
        task_path = self._create_task("001-valid-spec")
        report: SpecReadinessReport = check_task_specification(task_path, self.workspace)
        self.assertTrue(report.is_valid)
        self.assertEqual(len(report.diagnostics), 0)

    def test_task_missing_must_not_fails(self) -> None:
        self._setup_valid_context()
        task_path = self._create_task("002-missing-must-not", with_must_not=False)
        report = check_task_specification(task_path, self.workspace)
        self.assertFalse(report.is_valid)
        self.assertTrue(any(d.tool_name == "MISSING_MUST_NOT" for d in report.diagnostics))

    def test_task_missing_acceptance_criteria_fails(self) -> None:
        self._setup_valid_context()
        task_path = self._create_task("003-missing-criteria", with_criteria=False)
        report = check_task_specification(task_path, self.workspace)
        self.assertFalse(report.is_valid)
        self.assertTrue(
            any(d.tool_name == "MISSING_ACCEPTANCE_CRITERIA" for d in report.diagnostics)
        )

    def test_task_invalid_okf_fails(self) -> None:
        self._setup_valid_context()
        task_path = self.tasks_dir / "004-no-frontmatter.md"
        task_path.write_text(
            "# Task Without Frontmatter\n\n**Status**: `ACTIVE`\n\n## 🎯 Formål\nTest\n\n## 📋 Acceptance Criteria\n- [ ] test\n\n## 🚫 Must NOT\n- No\n",
            encoding="utf-8",
        )
        report = check_task_specification(task_path, self.workspace)
        self.assertFalse(report.is_valid)
        self.assertTrue(any(d.tool_name == "INVALID_OKF_METADATA" for d in report.diagnostics))

    def test_context_glossary_valid_passes(self) -> None:
        self._setup_valid_context()
        diagnostics = validate_context_glossary(self.workspace)
        self.assertEqual(len(diagnostics), 0)

    def test_context_glossary_invalid_format_fails(self) -> None:
        bad_context = (
            "---\n"
            "type: Knowledge Bundle Index\n"
            "title: Bad Glossary\n"
            "status: stable\n"
            "generated: { by: test, at: '2026-08-30T09:00:00Z' }\n"
            "---\n\n"
            "# Bad Glossary\n\n"
            "**Task**:\n"
            "An executable unit without avoid line.\n\n"
            "Missing bold title definition line.\n"
        )
        (self.workspace / "CONTEXT.md").write_text(bad_context, encoding="utf-8")
        diagnostics = validate_context_glossary(self.workspace)
        self.assertTrue(len(diagnostics) > 0)
        self.assertTrue(any("ARISTOTLE_FORMAT_VIOLATION" == d.tool_name for d in diagnostics))

    def test_gatekeeper_blocks_when_task_is_draft(self) -> None:
        self._setup_valid_context()
        self._create_task("005-draft-task", status="draft", with_must_not=False)
        engine = PolicyEngine()
        context = TrustedEnforcementContext(workspace_root=self.workspace)
        req = FileWriteRequest(
            target_file=self.src_dir / "app.py",
        )
        decision = engine.evaluate(req, context)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.verdict_code, GatekeeperVerdict.BLOCKED_NO_ACTIVE_TASK)

    def test_cli_check_spec_command_success(self) -> None:
        self._setup_valid_context()
        self._create_task("006-cli-success", status="active", with_must_not=True)
        code = main(["check-spec", "-w", str(self.workspace), "-t", "006-cli-success"])
        self.assertEqual(code, 0)

    def test_cli_check_spec_command_failure_and_json(self) -> None:
        self._setup_valid_context()
        self._create_task("007-cli-fail", status="active", with_must_not=False)
        code = main(["check-spec", "-w", str(self.workspace), "-t", "007-cli-fail", "--json"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
