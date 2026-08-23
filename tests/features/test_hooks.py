"""Tests for the surgical pre-invocation gatekeeper hook."""

import json
import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.hooks.gatekeeper import (
    GatekeeperVerdict,
    evaluate_tool_invocation,
)


class TestGatekeeperHook(unittest.TestCase):
    """Test suite for surgical gatekeeper hook."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        (self.workspace / "tasks").mkdir(parents=True)
        (self.workspace / "src").mkdir(parents=True)
        (self.workspace / "tests").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_allows_read_only_tools(self) -> None:
        """Read-only tools (view_file, list_dir, grep_search) are always allowed."""
        verdict = evaluate_tool_invocation(
            workspace=self.workspace,
            tool_name="view_file",
            tool_input={"AbsolutePath": str(self.workspace / "src" / "main.py")},
        )
        self.assertTrue(verdict.allowed)
        self.assertEqual(verdict.verdict_code, GatekeeperVerdict.ALLOW)

    def test_allows_editing_tasks_and_context(self) -> None:
        """Editing tasks/, CONTEXT.md, CLAUDE.md, ROADMAP.md, spec.md is always allowed."""
        verdict = evaluate_tool_invocation(
            workspace=self.workspace,
            tool_name="write_to_file",
            tool_input={"TargetFile": str(self.workspace / "tasks" / "001-init.md")},
        )
        self.assertTrue(verdict.allowed)

        for filename in ["CONTEXT.md", "CLAUDE.md", "ROADMAP.md", "spec.md"]:
            verdict_meta = evaluate_tool_invocation(
                workspace=self.workspace,
                tool_name="replace_file_content",
                tool_input={"TargetFile": str(self.workspace / filename)},
            )
            self.assertTrue(verdict_meta.allowed, f"Should allow editing {filename}")

    def test_blocks_src_edit_when_no_active_task_exists(self) -> None:
        """Modifying files in src/ or tests/ is blocked if no active task exists in tasks/."""
        verdict = evaluate_tool_invocation(
            workspace=self.workspace,
            tool_name="write_to_file",
            tool_input={"TargetFile": str(self.workspace / "src" / "code.py")},
        )
        self.assertFalse(verdict.allowed)
        self.assertEqual(verdict.verdict_code, GatekeeperVerdict.BLOCKED_NO_ACTIVE_TASK)
        self.assertIn("tasks/", verdict.reason.lower())

    def test_blocks_src_edit_when_task_is_not_active(self) -> None:
        """Modifying src/ is blocked if the only task is marked DONE."""
        task_file = self.workspace / "tasks" / "001-done.md"
        task_file.write_text("# Task 001\n\n**Status**: `DONE`\n\n## Acceptance Criteria\n- [x] Done\n")

        verdict = evaluate_tool_invocation(
            workspace=self.workspace,
            tool_name="replace_file_content",
            tool_input={"TargetFile": str(self.workspace / "src" / "code.py")},
        )
        self.assertFalse(verdict.allowed)
        self.assertEqual(verdict.verdict_code, GatekeeperVerdict.BLOCKED_NO_ACTIVE_TASK)

    def test_allows_src_edit_when_active_task_exists(self) -> None:
        """Modifying src/ is allowed when an active task with acceptance criteria exists."""
        task_file = self.workspace / "tasks" / "002-feature.md"
        task_file.write_text(
            "# Task 002: Feature\n\n**Status**: `ACTIVE`\n\n## Acceptance Criteria\n- [ ] Implement feature\n"
        )

        verdict = evaluate_tool_invocation(
            workspace=self.workspace,
            tool_name="write_to_file",
            tool_input={"TargetFile": str(self.workspace / "src" / "code.py")},
        )
        self.assertTrue(verdict.allowed)
        self.assertEqual(verdict.verdict_code, GatekeeperVerdict.ALLOW)

    def test_blocks_remote_git_push_commands(self) -> None:
        """Running git push is strictly blocked."""
        verdict = evaluate_tool_invocation(
            workspace=self.workspace,
            tool_name="run_command",
            tool_input={"CommandLine": "git push origin main"},
        )
        self.assertFalse(verdict.allowed)
        self.assertEqual(verdict.verdict_code, GatekeeperVerdict.BLOCKED_FORBIDDEN_COMMAND)
        self.assertIn("push", verdict.reason.lower())

    def test_allows_local_git_status_and_commit(self) -> None:
        """Local git status, diff, commit are allowed."""
        verdict = evaluate_tool_invocation(
            workspace=self.workspace,
            tool_name="run_command",
            tool_input={"CommandLine": "git status"},
        )
        self.assertTrue(verdict.allowed)
