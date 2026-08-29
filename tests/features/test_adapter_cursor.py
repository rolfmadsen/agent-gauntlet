"""Tests for Cursor IDE Adapter vertical slice, tool normalization, and rules bridge."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.adapters import get_adapter
from agent_gauntlet.features.adapters.cursor.adapter import CursorAdapter
from agent_gauntlet.features.adapters.cursor.validator import CursorRulesValidator
from agent_gauntlet.features.adapters.models import (
    ToolActionType,
)
from agent_gauntlet.features.scaffold.scaffolder import (
    DEFAULT_CURSOR_MDC,
    DEFAULT_CURSORRULES,
    ProjectScaffolder,
)


class TestCursorAdapterNormalization(unittest.TestCase):
    """Test suite for Cursor tool-call normalization."""

    def setUp(self) -> None:
        self.adapter = CursorAdapter()

    def test_normalize_command_execution_tools(self) -> None:
        """Cursor terminal/command execution tools are normalized to EXECUTE_COMMAND."""
        for tool_name in [
            "run_terminal_command",
            "run_command",
            "terminal",
            "bash",
            "execute_command",
            "command",
        ]:
            # Argument using 'command'
            payload_cmd = {
                "name": tool_name,
                "arguments": {"command": "pytest -v tests/"},
            }
            norm = self.adapter.normalize_tool_call(payload_cmd)
            self.assertEqual(norm.action_type, ToolActionType.EXECUTE_COMMAND)
            self.assertEqual(norm.target_resource, "pytest -v tests/")
            self.assertEqual(norm.raw_tool_name, tool_name)

            # Argument using 'CommandLine'
            payload_cl = {
                "toolCall": {
                    "name": tool_name,
                    "args": {"CommandLine": "python3 -m unittest discover"},
                }
            }
            norm_cl = self.adapter.normalize_tool_call(payload_cl)
            self.assertEqual(norm_cl.action_type, ToolActionType.EXECUTE_COMMAND)
            self.assertEqual(norm_cl.target_resource, "python3 -m unittest discover")

            # Argument using 'cmd'
            payload_short = {
                "tool_name": tool_name,
                "tool_input": {"cmd": "git status"},
            }
            norm_short = self.adapter.normalize_tool_call(payload_short)
            self.assertEqual(norm_short.action_type, ToolActionType.EXECUTE_COMMAND)
            self.assertEqual(norm_short.target_resource, "git status")

    def test_normalize_file_write_tools(self) -> None:
        """Cursor file creation and edit tools are normalized to WRITE_FILE."""
        for tool_name in [
            "write_file",
            "edit_file",
            "create_file",
            "update_file",
            "write_to_file",
            "replace_file_content",
            "multi_replace_file_content",
        ]:
            # Argument using 'path'
            payload_path = {
                "name": tool_name,
                "parameters": {"path": "src/agent_gauntlet/core.py"},
            }
            norm = self.adapter.normalize_tool_call(payload_path)
            self.assertEqual(norm.action_type, ToolActionType.WRITE_FILE)
            self.assertEqual(norm.target_resource, "src/agent_gauntlet/core.py")
            self.assertEqual(norm.raw_tool_name, tool_name)

            # Argument using 'target_file'
            payload_target = {
                "toolCall": {
                    "name": tool_name,
                    "args": {"target_file": "src/main.py"},
                }
            }
            norm_target = self.adapter.normalize_tool_call(payload_target)
            self.assertEqual(norm_target.action_type, ToolActionType.WRITE_FILE)
            self.assertEqual(norm_target.target_resource, "src/main.py")

            # Argument using 'TargetFile'
            payload_tf = {
                "tool_name": tool_name,
                "tool_input": {"TargetFile": "spec.md"},
            }
            norm_tf = self.adapter.normalize_tool_call(payload_tf)
            self.assertEqual(norm_tf.action_type, ToolActionType.WRITE_FILE)
            self.assertEqual(norm_tf.target_resource, "spec.md")

    def test_normalize_file_read_tools(self) -> None:
        """Cursor file reading and inspection tools are normalized to READ_FILE."""
        for tool_name in [
            "read_file",
            "view_file",
            "list_dir",
            "grep_search",
            "file_search",
            "read_dir",
            "find_by_name",
        ]:
            payload_read = {
                "name": tool_name,
                "arguments": {"path": "CONTEXT.md"},
            }
            norm = self.adapter.normalize_tool_call(payload_read)
            self.assertEqual(norm.action_type, ToolActionType.READ_FILE)
            self.assertEqual(norm.target_resource, "CONTEXT.md")

            payload_abs = {
                "toolCall": {
                    "name": tool_name,
                    "args": {"AbsolutePath": "/workspace/docs/adr/0001-architecture.md"},
                }
            }
            norm_abs = self.adapter.normalize_tool_call(payload_abs)
            self.assertEqual(norm_abs.action_type, ToolActionType.READ_FILE)
            self.assertEqual(norm_abs.target_resource, "/workspace/docs/adr/0001-architecture.md")

    def test_normalize_json_string_payload(self) -> None:
        """JSON string payloads are parsed and normalized correctly."""
        raw_json = json.dumps(
            {
                "tool_name": "run_terminal_command",
                "tool_input": {"command": "cargo check"},
            }
        )
        norm = self.adapter.normalize_tool_call(raw_json)
        self.assertEqual(norm.action_type, ToolActionType.EXECUTE_COMMAND)
        self.assertEqual(norm.target_resource, "cargo check")

    def test_normalize_malformed_and_unknown_payloads(self) -> None:
        """Malformed JSON strings, empty payloads, and unknown tools normalize to OTHER."""
        norm_corrupt = self.adapter.normalize_tool_call("{bad-json")
        self.assertEqual(norm_corrupt.action_type, ToolActionType.OTHER)
        self.assertEqual(norm_corrupt.target_resource, "")

        norm_empty = self.adapter.normalize_tool_call({})
        self.assertEqual(norm_empty.action_type, ToolActionType.OTHER)

        norm_unknown = self.adapter.normalize_tool_call(
            {"name": "custom_agent_thinking", "arguments": {"thought": "analyzing"}}
        )
        self.assertEqual(norm_unknown.action_type, ToolActionType.OTHER)
        self.assertEqual(norm_unknown.raw_tool_name, "custom_agent_thinking")


class TestCursorAdapterEvaluation(unittest.TestCase):
    """Test suite for Cursor invocation evaluation against gatekeeper invariants."""

    def setUp(self) -> None:
        self.adapter = CursorAdapter()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        # Create minimal workspace structure
        (self.workspace / "tasks").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_evaluate_blocks_forbidden_commands(self) -> None:
        """Dangerous commands like git push or git reset are blocked."""
        forbidden_commands = [
            "git push origin main",
            "git push --force",
            "git reset --hard HEAD~1",
            "git clean -fdx",
            "gh pr create --fill",
        ]
        for cmd in forbidden_commands:
            payload = {
                "name": "run_terminal_command",
                "arguments": {"command": cmd},
            }
            verdict = self.adapter.evaluate_invocation(self.workspace, payload)
            self.assertFalse(verdict.allowed, f"Expected {cmd} to be blocked")
            self.assertEqual(verdict.decision, "deny")
            self.assertIn("Forbidden Command", verdict.reason)

    def test_evaluate_allows_safe_verification_commands(self) -> None:
        """Safe verification commands are allowed."""
        safe_commands = [
            "pytest -v",
            "python3 -m unittest",
            "git status",
            "cargo test",
            "npm test",
        ]
        for cmd in safe_commands:
            payload = {
                "name": "run_terminal_command",
                "arguments": {"command": cmd},
            }
            verdict = self.adapter.evaluate_invocation(self.workspace, payload)
            self.assertTrue(verdict.allowed, f"Expected {cmd} to be allowed")
            self.assertEqual(verdict.decision, "allow")

    def test_evaluate_file_write_without_active_task_blocked(self) -> None:
        """File write operation without an active task in tasks/ is denied."""
        payload = {
            "name": "write_file",
            "arguments": {"path": "src/agent_gauntlet/core.py"},
        }
        verdict = self.adapter.evaluate_invocation(self.workspace, payload)
        self.assertFalse(verdict.allowed)
        self.assertEqual(verdict.decision, "deny")
        self.assertIn("Pre-Invocation Gate", verdict.reason)

    def test_evaluate_file_write_with_active_task_allowed(self) -> None:
        """File write operation with an active task in tasks/ is allowed."""
        task_file = self.workspace / "tasks/030-cursor-adapter.md"
        task_file.write_text(
            "# Task 030\n**Status**: `ACTIVE`\n\n## Acceptance Criteria\n- [ ] Implement feature\n",
            encoding="utf-8",
        )

        payload = {
            "name": "write_file",
            "arguments": {"path": "src/agent_gauntlet/core.py"},
        }
        verdict = self.adapter.evaluate_invocation(self.workspace, payload)
        self.assertTrue(verdict.allowed)
        self.assertEqual(verdict.decision, "allow")


class TestCursorRulesValidation(unittest.TestCase):
    """Test suite for Cursor rules validation (.cursor/rules/*.mdc)."""

    def setUp(self) -> None:
        self.validator = CursorRulesValidator()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.rules_dir = self.workspace / ".cursor/rules"
        self.rules_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_validate_valid_mdc_rule(self) -> None:
        """Valid .cursor/rules/agent-gauntlet.mdc passes validation."""
        rule_content = DEFAULT_CURSOR_MDC
        (self.rules_dir / "agent-gauntlet.mdc").write_text(rule_content, encoding="utf-8")

        res = self.validator.validate(self.workspace)
        self.assertTrue(res.valid, f"Expected valid, got issues: {res.issues}")
        self.assertEqual(len(res.issues), 0)

    def test_validate_missing_rules_directory_or_files(self) -> None:
        """Validation fails if no .mdc rule files exist."""
        empty_ws = Path(tempfile.mkdtemp())
        try:
            res = self.validator.validate(empty_ws)
            self.assertFalse(res.valid)
            self.assertTrue(
                any("No Cursor rule (.mdc) files found" in i.message for i in res.issues)
            )
        finally:
            import shutil

            shutil.rmtree(empty_ws, ignore_errors=True)

    def test_validate_mdc_missing_frontmatter(self) -> None:
        """Rule file without frontmatter fails validation."""
        (self.rules_dir / "broken.mdc").write_text("# Just Markdown without frontmatter\n")
        res = self.validator.validate(self.workspace)
        self.assertFalse(res.valid)
        self.assertTrue(any("frontmatter" in i.message.lower() for i in res.issues))

    def test_validate_mdc_missing_required_fields(self) -> None:
        """Missing description, globs, or alwaysApply in frontmatter fails validation."""
        bad_frontmatter = """---
description: "Incomplete rule"
---
# Content
"""
        (self.rules_dir / "incomplete.mdc").write_text(bad_frontmatter, encoding="utf-8")
        res = self.validator.validate(self.workspace)
        self.assertFalse(res.valid)
        messages = [i.message for i in res.issues]
        self.assertTrue(any("globs" in m for m in messages))
        self.assertTrue(
            any("missing required boolean property 'alwaysApply'" in m for m in messages)
        )

    def test_validate_mdc_invalid_always_apply_type(self) -> None:
        """Non-boolean alwaysApply field fails validation."""
        bad_type = """---
description: "Rule with string alwaysApply"
globs: "*"
alwaysApply: "yes"
---
# Content
"""
        (self.rules_dir / "bad_type.mdc").write_text(bad_type, encoding="utf-8")
        res = self.validator.validate(self.workspace)
        self.assertFalse(res.valid)
        self.assertTrue(any("boolean" in i.message.lower() for i in res.issues))


class TestCursorScaffolding(unittest.TestCase):
    """Test suite for Cursor rules scaffolding via ProjectScaffolder."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.scaffolder = ProjectScaffolder()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_scaffold_with_cursor_harness(self) -> None:
        """Scaffolding with harness='cursor' creates .cursor/rules/agent-gauntlet.mdc and .cursorrules."""
        result = self.scaffolder.scaffold(
            self.workspace, stack="python", harness="cursor", config_format="toml"
        )
        self.assertTrue(result.success)
        self.assertEqual(result.harness, "cursor")

        mdc_path = self.workspace / ".cursor/rules/agent-gauntlet.mdc"
        cursorrules_path = self.workspace / ".cursorrules"

        self.assertTrue(mdc_path.is_file(), "Expected .cursor/rules/agent-gauntlet.mdc to exist")
        self.assertTrue(cursorrules_path.is_file(), "Expected .cursorrules to exist")

        mdc_content = mdc_path.read_text(encoding="utf-8")
        self.assertIn("alwaysApply: true", mdc_content)
        self.assertIn('globs: "*"', mdc_content)
        self.assertIn(".agents/AGENTS.md", mdc_content)
        self.assertIn("CODING_STANDARDS.md", mdc_content)

        cursorrules_content = cursorrules_path.read_text(encoding="utf-8")
        self.assertIn(".agents/AGENTS.md", cursorrules_content)
        self.assertIn("CODING_STANDARDS.md", cursorrules_content)

    def test_cursor_rules_templates(self) -> None:
        """Default Cursor MDC and legacy cursorrules templates contain authoritative references."""
        self.assertIn("alwaysApply: true", DEFAULT_CURSOR_MDC)
        self.assertIn(".agents/AGENTS.md", DEFAULT_CURSOR_MDC)
        self.assertIn(".agents/AGENTS.md", DEFAULT_CURSORRULES)
        self.assertIn("CODING_STANDARDS.md", DEFAULT_CURSORRULES)

    def test_cursor_adapter_registered_in_registry(self) -> None:
        """get_adapter('cursor') resolves CursorAdapter."""
        adapter = get_adapter("cursor")
        self.assertIsInstance(adapter, CursorAdapter)
        self.assertEqual(adapter.name, "cursor")


if __name__ == "__main__":
    unittest.main()
