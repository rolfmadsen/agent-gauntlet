"""Tests for WASM Policy Verifier, deterministic evaluation, digest validation, and zero ambient authority."""

import unittest

from agent_gauntlet.features.supervisor.core.models import (
    CapabilityRequest,
    DecisionVerdict,
    EnforcementContext,
    ToolActionType,
)
from agent_gauntlet.features.supervisor.wasm.verifier import (
    WasmDigestMismatchError,
    WasmPolicyVerifier,
)


class TestWasmPolicyVerifier(unittest.TestCase):
    """Verifies deterministic policy evaluation, digest checking, and zero ambient authority."""

    def setUp(self) -> None:
        self.verifier = WasmPolicyVerifier()

    def test_digest_verification_rejects_tampered_component(self) -> None:
        """Loading a component with mismatched digest fails closed with WasmDigestMismatchError."""
        with self.assertRaises(WasmDigestMismatchError):
            self.verifier.load_component(
                wasm_bytes=b"\x00asm\x01\x00\x00\x00tampered",
                expected_digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
            )

    def test_read_operations_always_allowed(self) -> None:
        """Reading files or documentation is allowed regardless of task state."""
        req = CapabilityRequest(
            action_type=ToolActionType.READ_FILE,
            raw_tool_name="view_file",
            target_resource="src/core.py",
        )
        ctx = EnforcementContext(
            workspace_id="ws-1",
            has_active_task=False,
            active_task_id="",
            read_only=False,
        )
        decision = self.verifier.evaluate(req, ctx)
        self.assertEqual(decision.verdict, DecisionVerdict.ALLOW)

    def test_write_to_production_code_without_active_task_denied(self) -> None:
        """Writing to src/ or tests/ without an active task is denied fail-closed."""
        req = CapabilityRequest(
            action_type=ToolActionType.WRITE_FILE,
            raw_tool_name="write_to_file",
            target_resource="src/features/new.py",
        )
        ctx = EnforcementContext(
            workspace_id="ws-1",
            has_active_task=False,
            active_task_id="",
            read_only=False,
        )
        decision = self.verifier.evaluate(req, ctx)
        self.assertEqual(decision.verdict, DecisionVerdict.DENY)
        self.assertEqual(decision.reason_code, 4031)

    def test_write_to_production_code_with_active_task_allowed(self) -> None:
        """Writing to src/ or tests/ with an active task is allowed."""
        req = CapabilityRequest(
            action_type=ToolActionType.WRITE_FILE,
            raw_tool_name="write_to_file",
            target_resource="src/features/new.py",
        )
        ctx = EnforcementContext(
            workspace_id="ws-1",
            has_active_task=True,
            active_task_id="035-supervisor",
            read_only=False,
        )
        decision = self.verifier.evaluate(req, ctx)
        self.assertEqual(decision.verdict, DecisionVerdict.ALLOW)

    def test_write_to_tasks_and_spec_always_allowed(self) -> None:
        """Writing to tasks/, spec.md, or CONTEXT.md is allowed even without an active task."""
        for target in ("tasks/001-test.md", "spec.md", "CONTEXT.md"):
            req = CapabilityRequest(
                action_type=ToolActionType.WRITE_FILE,
                raw_tool_name="write_to_file",
                target_resource=target,
            )
            ctx = EnforcementContext(
                workspace_id="ws-1",
                has_active_task=False,
                active_task_id="",
                read_only=False,
            )
            decision = self.verifier.evaluate(req, ctx)
            self.assertEqual(
                decision.verdict, DecisionVerdict.ALLOW, f"Expected {target} to be writable"
            )

    def test_read_only_mode_denies_all_mutations(self) -> None:
        """When read_only is True, all write and mutation requests are denied."""
        req = CapabilityRequest(
            action_type=ToolActionType.WRITE_FILE,
            raw_tool_name="write_to_file",
            target_resource="tasks/001-test.md",
        )
        ctx = EnforcementContext(
            workspace_id="ws-1",
            has_active_task=True,
            active_task_id="035-supervisor",
            read_only=True,
        )
        decision = self.verifier.evaluate(req, ctx)
        self.assertEqual(decision.verdict, DecisionVerdict.DENY)

    def test_deterministic_evaluation_property(self) -> None:
        """Identical inputs produce identical typed outputs across multiple evaluations."""
        req = CapabilityRequest(
            action_type=ToolActionType.WRITE_FILE,
            raw_tool_name="write_to_file",
            target_resource="src/app.py",
        )
        ctx = EnforcementContext(
            workspace_id="ws-1",
            has_active_task=False,
            active_task_id="",
            read_only=False,
        )
        d1 = self.verifier.evaluate(req, ctx)
        d2 = self.verifier.evaluate(req, ctx)
        self.assertEqual(d1, d2)


if __name__ == "__main__":
    unittest.main()
