"""Tests for SupervisorEngine, RPC dispatching, session management, and report generation."""

import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.supervisor.core.engine import SupervisorEngine
from agent_gauntlet.features.supervisor.core.models import (
    DecisionVerdict,
    RpcMethod,
    RpcRequest,
    SessionState,
)
from agent_gauntlet.features.supervisor.platform.linux.keys import LinuxKeyProvider


class TestSupervisorEngine(unittest.TestCase):
    """Verifies that SupervisorEngine handles RPC calls, manages sessions, and produces signed reports."""

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

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_get_status_rpc(self) -> None:
        """GetStatus returns supervisor health, active sessions count, and version."""
        req = RpcRequest(id="1", method=RpcMethod.GET_STATUS)
        res = self.engine.handle_rpc(req)
        self.assertTrue(res.is_success)
        self.assertIsNotNone(res.result)
        assert res.result is not None
        self.assertEqual(res.result["status"], "HEALTHY")
        self.assertEqual(res.result["version"], "0.6.0")
        self.assertTrue("installation_public_key" in res.result)

    def test_register_workspace_and_begin_session(self) -> None:
        """RegisterWorkspace and BeginOrResumeSession activate a task session."""
        reg_req = RpcRequest(
            id="2",
            method=RpcMethod.REGISTER_WORKSPACE,
            params={"workspace_path": str(self.workspace), "workspace_id": "ws-1"},
        )
        reg_res = self.engine.handle_rpc(reg_req)
        self.assertTrue(reg_res.is_success)

        begin_req = RpcRequest(
            id="3",
            method=RpcMethod.BEGIN_OR_RESUME_SESSION,
            params={"workspace_id": "ws-1", "task_id": "035-test"},
        )
        begin_res = self.engine.handle_rpc(begin_req)
        self.assertTrue(begin_res.is_success)
        self.assertIsNotNone(begin_res.result)
        assert begin_res.result is not None
        self.assertEqual(begin_res.result["state"], SessionState.ACTIVE.value)
        self.assertTrue(begin_res.result["task_certificate"])

    def test_evaluate_tool_call_rpc(self) -> None:
        """EvaluateToolCall evaluates requests against WASM verifier and records event."""
        # First activate session
        self.engine.register_workspace(str(self.workspace), "ws-1")
        self.engine.begin_or_resume_session("ws-1", "035-test")

        eval_req = RpcRequest(
            id="4",
            method=RpcMethod.EVALUATE_TOOL_CALL,
            params={
                "workspace_id": "ws-1",
                "request": {
                    "action_type": "write_file",
                    "raw_tool_name": "write_to_file",
                    "target_resource": "src/app.py",
                    "payload_json": "{}",
                },
            },
        )
        eval_res = self.engine.handle_rpc(eval_req)
        self.assertTrue(eval_res.is_success)
        self.assertIsNotNone(eval_res.result)
        assert eval_res.result is not None
        self.assertEqual(eval_res.result["decision"]["verdict"], DecisionVerdict.ALLOW.value)


if __name__ == "__main__":
    unittest.main()
