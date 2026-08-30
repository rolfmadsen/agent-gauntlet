"""Tests for portable supervisor RPC contracts, capability models, and policy verdicts."""

import unittest

from agent_gauntlet.features.supervisor.core.models import (
    CapabilityRequest,
    DecisionVerdict,
    EnforcementContext,
    PolicyDecision,
    RpcMethod,
    RpcRequest,
    RpcResponse,
    ToolActionType,
)


class TestSupervisorContracts(unittest.TestCase):
    """Verifies that supervisor RPC contracts and data models serialize deterministically."""

    def test_tool_action_type_values(self) -> None:
        """Validates tool action types match the WIT enum contract."""
        self.assertEqual(ToolActionType.READ_FILE.value, "read_file")
        self.assertEqual(ToolActionType.WRITE_FILE.value, "write_file")
        self.assertEqual(ToolActionType.EXECUTE_COMMAND.value, "execute_command")
        self.assertEqual(ToolActionType.OTHER.value, "other")

    def test_decision_verdict_values(self) -> None:
        """Validates decision verdicts match the WIT enum contract."""
        self.assertEqual(DecisionVerdict.ALLOW.value, "allow")
        self.assertEqual(DecisionVerdict.DENY.value, "deny")
        self.assertEqual(DecisionVerdict.ASK.value, "ask")
        self.assertEqual(DecisionVerdict.FORCE_ASK.value, "force_ask")

    def test_capability_request_serialization(self) -> None:
        """CapabilityRequest serializes to dict and JSON without data loss."""
        req = CapabilityRequest(
            action_type=ToolActionType.WRITE_FILE,
            raw_tool_name="write_to_file",
            target_resource="src/core.py",
            payload_json='{"content": "abc"}',
        )
        data = req.to_dict()
        self.assertEqual(data["action_type"], "write_file")
        self.assertEqual(data["target_resource"], "src/core.py")
        self.assertEqual(data["raw_tool_name"], "write_to_file")

        # Roundtrip test
        reconstructed = CapabilityRequest.from_dict(data)
        self.assertEqual(reconstructed, req)

    def test_enforcement_context_immutability(self) -> None:
        """EnforcementContext is frozen and cannot be mutated by callers."""
        ctx = EnforcementContext(
            workspace_id="ws-123",
            has_active_task=True,
            active_task_id="035-test",
            read_only=False,
        )
        with self.assertRaises(Exception):
            ctx.read_only = True  # type: ignore

    def test_policy_decision_serialization(self) -> None:
        """PolicyDecision serializes with correct verdict and reason code."""
        dec = PolicyDecision(
            verdict=DecisionVerdict.DENY,
            reason="Writing to production code without active task is prohibited.",
            reason_code=4031,
        )
        data = dec.to_dict()
        self.assertEqual(data["verdict"], "deny")
        self.assertEqual(data["reason_code"], 4031)
        self.assertEqual(PolicyDecision.from_dict(data), dec)

    def test_rpc_request_and_response_envelope(self) -> None:
        """RPC envelope handles typed requests and responses."""
        rpc_req = RpcRequest(
            id="req-1",
            method=RpcMethod.EVALUATE_TOOL_CALL,
            params={
                "request": {
                    "action_type": "write_file",
                    "raw_tool_name": "write_to_file",
                    "target_resource": "src/app.py",
                    "payload_json": "{}",
                },
                "context": {
                    "workspace_id": "ws-1",
                    "has_active_task": False,
                    "active_task_id": "",
                    "read_only": False,
                },
            },
        )
        json_str = rpc_req.to_json()
        parsed = RpcRequest.from_json(json_str)
        self.assertEqual(parsed.id, "req-1")
        self.assertEqual(parsed.method, RpcMethod.EVALUATE_TOOL_CALL)

        rpc_res = RpcResponse(
            id="req-1",
            result={"verdict": "deny", "reason": "No active task", "reason_code": 4030},
            error=None,
        )
        self.assertTrue(rpc_res.is_success)
        self.assertIn('"verdict": "deny"', rpc_res.to_json())


if __name__ == "__main__":
    unittest.main()
