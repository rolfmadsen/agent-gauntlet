"""Tests for Google Antigravity Adapter vertical slice."""

import io
import json
import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.adapters.antigravity.adapter import AntigravityAdapter
from agent_gauntlet.features.adapters.antigravity.hook import main_hook_entrypoint
from agent_gauntlet.features.adapters.antigravity.validator import AntigravityPluginValidator
from agent_gauntlet.features.adapters.models import (
    ToolActionType,
)


class TestAntigravityAdapterNormalization(unittest.TestCase):
    """Test suite for Antigravity tool-call normalization."""

    def setUp(self) -> None:
        self.adapter = AntigravityAdapter()

    def test_normalize_pre_tool_use_run_command(self) -> None:
        """Canonical PreToolUse run_command payload is mapped to EXECUTE_COMMAND."""
        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": "pytest tests/test_core.py",
                },
            },
            "workspacePaths": ["/workspace"],
        }
        normalized = self.adapter.normalize_tool_call(payload)
        self.assertEqual(normalized.action_type, ToolActionType.EXECUTE_COMMAND)
        self.assertEqual(normalized.target_resource, "pytest tests/test_core.py")
        self.assertEqual(normalized.raw_tool_name, "run_command")

    def test_normalize_pre_tool_use_write_files(self) -> None:
        """Canonical PreToolUse file editing tools are mapped to WRITE_FILE."""
        for tool_name in ["write_to_file", "replace_file_content", "multi_replace_file_content"]:
            payload = {
                "toolCall": {
                    "name": tool_name,
                    "args": {
                        "TargetFile": "/workspace/src/app.py",
                    },
                }
            }
            normalized = self.adapter.normalize_tool_call(payload)
            self.assertEqual(normalized.action_type, ToolActionType.WRITE_FILE)
            self.assertEqual(normalized.target_resource, "/workspace/src/app.py")
            self.assertEqual(normalized.raw_tool_name, tool_name)

    def test_normalize_pre_tool_use_read_only(self) -> None:
        """Read tools like view_file, list_dir, grep_search are mapped to READ_FILE."""
        for tool_name in ["view_file", "list_dir", "grep_search"]:
            payload = {
                "toolCall": {
                    "name": tool_name,
                    "args": {
                        "AbsolutePath": "/workspace/README.md",
                    },
                }
            }
            normalized = self.adapter.normalize_tool_call(payload)
            self.assertEqual(normalized.action_type, ToolActionType.READ_FILE)

    def test_normalize_legacy_flat_payloads(self) -> None:
        """Legacy flat payloads ({'tool_name': ..., 'tool_input': ...}) are correctly normalized."""
        cmd_payload = {
            "tool_name": "run_command",
            "tool_input": {"CommandLine": "git status"},
        }
        norm_cmd = self.adapter.normalize_tool_call(cmd_payload)
        self.assertEqual(norm_cmd.action_type, ToolActionType.EXECUTE_COMMAND)
        self.assertEqual(norm_cmd.target_resource, "git status")

        file_payload = {
            "tool_name": "write_to_file",
            "tool_input": {"TargetFile": "src/main.py"},
        }
        norm_file = self.adapter.normalize_tool_call(file_payload)
        self.assertEqual(norm_file.action_type, ToolActionType.WRITE_FILE)
        self.assertEqual(norm_file.target_resource, "src/main.py")

    def test_normalize_unknown_or_malformed_payload(self) -> None:
        """Unknown or empty payloads default to OTHER."""
        norm_unknown = self.adapter.normalize_tool_call({"toolCall": {"name": "custom_mcp_tool"}})
        self.assertEqual(norm_unknown.action_type, ToolActionType.OTHER)

        norm_empty = self.adapter.normalize_tool_call({})
        self.assertEqual(norm_empty.action_type, ToolActionType.OTHER)


class TestAntigravityAdapterEvaluation(unittest.TestCase):
    """Test suite for Antigravity invocation evaluation against gatekeeper rules."""

    def setUp(self) -> None:
        self.adapter = AntigravityAdapter()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        (self.workspace / "tasks").mkdir(parents=True)
        (self.workspace / "src").mkdir(parents=True)
        (self.workspace / "tests").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_allows_read_only_tool_invocation(self) -> None:
        """Evaluating read-only tool invocation returns decision='allow'."""
        payload = {
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": str(self.workspace / "src/main.py")},
            }
        }
        res = self.adapter.evaluate_invocation(self.workspace, payload)
        self.assertTrue(res.allowed)
        self.assertEqual(res.decision, "allow")

    def test_blocks_forbidden_remote_command(self) -> None:
        """Forbidden remote commands (git push) are blocked with decision='deny'."""
        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git push origin main"},
            }
        }
        res = self.adapter.evaluate_invocation(self.workspace, payload)
        self.assertFalse(res.allowed)
        self.assertEqual(res.decision, "deny")
        self.assertIn("push", res.reason.lower())

    def test_blocks_src_edit_when_no_active_task(self) -> None:
        """Editing src/ without an active task in tasks/ is blocked with decision='deny'."""
        payload = {
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": str(self.workspace / "src/main.py")},
            }
        }
        res = self.adapter.evaluate_invocation(self.workspace, payload)
        self.assertFalse(res.allowed)
        self.assertEqual(res.decision, "deny")
        self.assertIn("tasks/", res.reason.lower())

    def test_allows_src_edit_when_active_task_exists(self) -> None:
        """Editing src/ is allowed when an active task exists."""
        task_file = self.workspace / "tasks" / "001-feature.md"
        task_file.write_text("# Task 001: Feature\n\n**Status**: `ACTIVE`\n\n## Acceptance Criteria\n- [ ] Do it\n")

        payload = {
            "toolCall": {
                "name": "replace_file_content",
                "args": {"TargetFile": str(self.workspace / "src/main.py")},
            }
        }
        res = self.adapter.evaluate_invocation(self.workspace, payload)
        self.assertTrue(res.allowed)
        self.assertEqual(res.decision, "allow")

    def test_allows_editing_metadata_and_tasks_without_active_task(self) -> None:
        """Editing tasks/, docs/, CONTEXT.md, spec.md is always allowed."""
        for target in ["tasks/001.md", "CONTEXT.md", "spec.md", "ROADMAP.md", "CLAUDE.md"]:
            payload = {
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": str(self.workspace / target)},
                }
            }
            res = self.adapter.evaluate_invocation(self.workspace, payload)
            self.assertTrue(res.allowed, f"Should allow editing {target}")


class TestAntigravityPluginValidator(unittest.TestCase):
    """Test suite for mechanical validation of Antigravity plugin structure."""

    def setUp(self) -> None:
        self.validator = AntigravityPluginValidator()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.plugin_dir = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _scaffold_valid_plugin(self) -> None:
        plugin_json = {
            "name": "agent-gauntlet",
            "version": "0.2.0",
            "description": "Test plugin",
            "skills": ["old-coder", "grill-me"],
            "entrypoints": {
                "gatekeeper": "agent_gauntlet.features.hooks.gatekeeper:main_hook_entrypoint",
            },
        }
        (self.plugin_dir / "plugin.json").write_text(json.dumps(plugin_json))

        hooks_json = {
            "pre_tool_invocation": {
                "command": ["python3", "-m", "agent_gauntlet.features.hooks.gatekeeper"]
            }
        }
        (self.plugin_dir / "hooks.json").write_text(json.dumps(hooks_json))

        # Skills
        for skill_name in ["old-coder", "grill-me"]:
            skill_dir = self.plugin_dir / "skills" / skill_name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {skill_name}\ndescription: Test description\n---\n# {skill_name}\n"
            )

    def test_validates_actual_repo_plugin(self) -> None:
        """Validates that the repo's actual plugins/agent-gauntlet is valid."""
        repo_plugin_dir = Path(__file__).resolve().parent.parent.parent / "plugins/agent-gauntlet"
        if repo_plugin_dir.is_dir():
            res = self.validator.validate(repo_plugin_dir)
            self.assertTrue(res.valid, f"Repo plugin should be valid, got issues: {res.issues}")
            self.assertEqual(len(res.issues), 0)

    def test_valid_scaffolded_plugin_passes(self) -> None:
        """A properly scaffolded plugin passes validation."""
        self._scaffold_valid_plugin()
        res = self.validator.validate(self.plugin_dir)
        self.assertTrue(res.valid)
        self.assertEqual(len(res.issues), 0)

    def test_missing_plugin_json_fails(self) -> None:
        """Missing plugin.json reports an error issue."""
        res = self.validator.validate(self.plugin_dir)
        self.assertFalse(res.valid)
        self.assertTrue(any(i.path == "plugin.json" and "Missing required manifest" in i.message for i in res.issues))

    def test_corrupt_plugin_json_fails(self) -> None:
        """Corrupt JSON in plugin.json reports an error."""
        (self.plugin_dir / "plugin.json").write_text("{not-valid-json")
        res = self.validator.validate(self.plugin_dir)
        self.assertFalse(res.valid)
        self.assertTrue(any("json" in i.message.lower() for i in res.issues))

    def test_missing_required_fields_in_plugin_json(self) -> None:
        """Missing version or name reports validation error."""
        (self.plugin_dir / "plugin.json").write_text(json.dumps({"name": "test"}))
        res = self.validator.validate(self.plugin_dir)
        self.assertFalse(res.valid)
        self.assertTrue(any("version" in i.message.lower() for i in res.issues))

    def test_missing_declared_skill_fails(self) -> None:
        """Declared skill missing SKILL.md reports an error."""
        self._scaffold_valid_plugin()
        # Declare nonexistent skill
        p_json = json.loads((self.plugin_dir / "plugin.json").read_text())
        p_json["skills"].append("nonexistent-skill")
        (self.plugin_dir / "plugin.json").write_text(json.dumps(p_json))

        res = self.validator.validate(self.plugin_dir)
        self.assertFalse(res.valid)
        self.assertTrue(any("missing 'SKILL.md' file" in i.message for i in res.issues))

    def test_skill_missing_frontmatter_fails(self) -> None:
        """Skill without frontmatter in SKILL.md reports an error."""
        self._scaffold_valid_plugin()
        (self.plugin_dir / "skills/old-coder/SKILL.md").write_text("# Old Coder without frontmatter")
        res = self.validator.validate(self.plugin_dir)
        self.assertFalse(res.valid)
        self.assertTrue(any("frontmatter" in i.message.lower() for i in res.issues))

    def test_invalid_entrypoint_reference_fails(self) -> None:
        """Entrypoint pointing to nonexistent module reports an error."""
        self._scaffold_valid_plugin()
        p_json = json.loads((self.plugin_dir / "plugin.json").read_text())
        p_json["entrypoints"]["broken"] = "agent_gauntlet.nonexistent.module:func"
        (self.plugin_dir / "plugin.json").write_text(json.dumps(p_json))

        res = self.validator.validate(self.plugin_dir)
        self.assertFalse(res.valid)
        self.assertTrue(any("broken" in i.message or "nonexistent" in i.message for i in res.issues))


class TestAntigravityHookCli(unittest.TestCase):
    """Test suite for Antigravity PreInvocation CLI hook entrypoint."""

    def test_hook_cli_blocks_forbidden_command(self) -> None:
        """Hook CLI outputs deny JSON and returns exit code 1 on git push."""
        stdin_data = json.dumps({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git push origin main"},
            }
        })
        stdin_stream = io.StringIO(stdin_data)
        stdout_stream = io.StringIO()
        stderr_stream = io.StringIO()

        code = main_hook_entrypoint(
            argv=[],
            stdin=stdin_stream,
            stdout=stdout_stream,
            stderr=stderr_stream,
            workspace=Path("/tmp"),
        )
        self.assertEqual(code, 1)
        out = json.loads(stdout_stream.getvalue().strip())
        self.assertEqual(out["decision"], "deny")
        self.assertIn("push", out["reason"].lower())

    def test_hook_cli_allows_safe_command(self) -> None:
        """Hook CLI outputs allow JSON and returns exit code 0 on git status."""
        stdin_data = json.dumps({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git status"},
            }
        })
        stdin_stream = io.StringIO(stdin_data)
        stdout_stream = io.StringIO()
        stderr_stream = io.StringIO()

        code = main_hook_entrypoint(
            argv=[],
            stdin=stdin_stream,
            stdout=stdout_stream,
            stderr=stderr_stream,
            workspace=Path("/tmp"),
        )
        self.assertEqual(code, 0)
        out = json.loads(stdout_stream.getvalue().strip())
        self.assertEqual(out["decision"], "allow")

    def test_hook_cli_fails_closed_on_empty_input(self) -> None:
        """Hook CLI fails closed (exit code 1, decision: deny) on empty stdin."""
        stdin_stream = io.StringIO("")
        stdout_stream = io.StringIO()
        stderr_stream = io.StringIO()

        code = main_hook_entrypoint(
            argv=[],
            stdin=stdin_stream,
            stdout=stdout_stream,
            stderr=stderr_stream,
            workspace=Path("/tmp"),
        )
        self.assertEqual(code, 1)
        out = json.loads(stdout_stream.getvalue().strip())
        self.assertEqual(out["decision"], "deny")

    def test_hook_cli_fails_closed_on_corrupt_json(self) -> None:
        """Hook CLI fails closed (exit code 1, decision: deny) on corrupted JSON."""
        stdin_stream = io.StringIO("{broken json")
        stdout_stream = io.StringIO()
        stderr_stream = io.StringIO()

        code = main_hook_entrypoint(
            argv=[],
            stdin=stdin_stream,
            stdout=stdout_stream,
            stderr=stderr_stream,
            workspace=Path("/tmp"),
        )
        self.assertEqual(code, 1)
        out = json.loads(stdout_stream.getvalue().strip())
        self.assertEqual(out["decision"], "deny")

    def test_subprocess_hook_denial_contract(self) -> None:
        """Integration: Invoking hook module via real subprocess enforces exit code 1 and stdout JSON deny."""
        import os
        import subprocess
        import sys

        repo_root = Path(__file__).resolve().parent.parent.parent
        env = {
            **os.environ,
            "PYTHONPATH": f"{repo_root / 'src'}:{os.environ.get('PYTHONPATH', '')}",
        }
        payload = json.dumps({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git push origin main"},
            }
        })
        proc = subprocess.run(
            [sys.executable, "-m", "agent_gauntlet.features.adapters.antigravity.hook"],
            input=payload,
            capture_output=True,
            text=True,
            cwd=repo_root,
            env=env,
        )
        self.assertEqual(proc.returncode, 1, "Denial must result in exit code 1")
        stdout_data = json.loads(proc.stdout.strip())
        self.assertEqual(stdout_data["decision"], "deny")
        self.assertIn("push", stdout_data["reason"].lower())

    def test_subprocess_hook_allow_contract(self) -> None:
        """Integration: Invoking hook module via real subprocess returns exit code 0 and stdout JSON allow."""
        import os
        import subprocess
        import sys

        repo_root = Path(__file__).resolve().parent.parent.parent
        env = {
            **os.environ,
            "PYTHONPATH": f"{repo_root / 'src'}:{os.environ.get('PYTHONPATH', '')}",
        }
        payload = json.dumps({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git status"},
            }
        })
        proc = subprocess.run(
            [sys.executable, "-m", "agent_gauntlet.features.adapters.antigravity.hook"],
            input=payload,
            capture_output=True,
            text=True,
            cwd=repo_root,
            env=env,
        )
        self.assertEqual(proc.returncode, 0, "Allow must result in exit code 0")
        stdout_data = json.loads(proc.stdout.strip())
        self.assertEqual(stdout_data["decision"], "allow")
