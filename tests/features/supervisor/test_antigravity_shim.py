"""Tests for Global Antigravity Hook Shim and IPC socket translation."""

import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.adapters.antigravity.shim import AntigravityHookShim
from agent_gauntlet.features.supervisor.core.engine import SupervisorEngine
from agent_gauntlet.features.supervisor.core.models import RpcRequest, RpcResponse
from agent_gauntlet.features.supervisor.platform.linux.keys import LinuxKeyProvider


class MockIpcTransport:
    """Mock IPC transport simulating local supervisor daemon responses."""

    def __init__(self, engine: SupervisorEngine) -> None:
        self.engine = engine

    def get_socket_endpoint(self) -> str:
        return "mock://supervisor"

    def send_rpc(self, request: RpcRequest, timeout_seconds: float = 2.0) -> RpcResponse:
        return self.engine.handle_rpc(request)


class TestAntigravityHookShim(unittest.TestCase):
    """Verifies that AntigravityHookShim translates IDE payloads and handles supervisor responses."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp_dir.name)
        (self.workspace / "tasks").mkdir()
        (self.workspace / "tasks" / "035-test.md").write_text("# Task 035", encoding="utf-8")
        (self.workspace / "src").mkdir()
        (self.workspace / "src" / "app.py").write_text("x = 1", encoding="utf-8")

        self.key_dir = self.workspace / ".keys"
        self.key_provider = LinuxKeyProvider(key_storage_dir=self.key_dir)
        self.engine = SupervisorEngine(key_provider=self.key_provider)
        self.engine.register_workspace(str(self.workspace), "ws-1")
        self.engine.begin_or_resume_session("ws-1", "035-test")

        self.transport = MockIpcTransport(self.engine)
        self.shim = AntigravityHookShim(transport=self.transport)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_pre_tool_use_write_allowed_under_active_task(self) -> None:
        """PreToolUse with write_to_file under active task returns allow decision."""
        payload = {
            "conversationId": "conv-1",
            "workspacePaths": [str(self.workspace)],
            "stepIdx": 1,
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": "src/app.py", "CodeContent": "x = 2"},
            },
        }
        res = self.shim.handle_hook(payload, workspace_id="ws-1")
        self.assertEqual(res.get("decision"), "allow")

    def test_pre_tool_use_write_denied_without_task(self) -> None:
        """PreToolUse with write_to_file without active task returns deny decision."""
        # Create empty workspace without task
        empty_dir = Path(tempfile.mkdtemp())
        self.engine.register_workspace(str(empty_dir), "ws-empty")

        payload = {
            "conversationId": "conv-2",
            "workspacePaths": [str(empty_dir)],
            "stepIdx": 1,
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": "src/app.py", "CodeContent": "x = 2"},
            },
        }
        res = self.shim.handle_hook(payload, workspace_id="ws-empty")
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("prohibited", res.get("reason", "").lower())

    def test_supervisor_unavailable_fails_closed_on_writes(self) -> None:
        """When supervisor IPC is unavailable, writes fail closed and reads succeed with warning."""
        offline_shim = AntigravityHookShim(transport=None)  # No transport available

        write_payload = {
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": "src/app.py"},
            }
        }
        res_write = offline_shim.handle_hook(write_payload, workspace_id="ws-1")
        self.assertEqual(res_write.get("decision"), "deny")
        self.assertIn("unavailable", res_write.get("reason", "").lower())

        read_payload = {
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": "src/app.py"},
            }
        }
        res_read = offline_shim.handle_hook(read_payload, workspace_id="ws-1")
        self.assertEqual(res_read.get("decision"), "allow")


if __name__ == "__main__":
    unittest.main()
