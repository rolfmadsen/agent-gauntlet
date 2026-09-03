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

    def test_real_native_and_wasm_execution(self) -> None:
        """Tests that native .so and wasm runtimes execute and produce identical verdicts."""
        self.assertTrue(self.verifier.is_native_loaded)
        self.assertTrue(self.verifier.is_wasm_loaded)
        self.assertTrue(self.verifier.loaded_digest.startswith("sha256:"))

        req_deny = CapabilityRequest(
            action_type=ToolActionType.WRITE_FILE,
            raw_tool_name="write_to_file",
            target_resource="src/app.py",
        )
        ctx_no_task = EnforcementContext(
            workspace_id="ws-1",
            has_active_task=False,
            active_task_id="",
            read_only=False,
        )
        native_dec = self.verifier.evaluate_native(req_deny, ctx_no_task)
        wasm_dec = self.verifier.evaluate_wasm(req_deny, ctx_no_task)
        self.assertEqual(native_dec.verdict, DecisionVerdict.DENY)
        self.assertEqual(native_dec.reason_code, 4031)
        self.assertEqual(wasm_dec.verdict, DecisionVerdict.DENY)
        self.assertEqual(wasm_dec.reason_code, 4031)
        self.assertEqual(native_dec, wasm_dec)

        ctx_active = EnforcementContext(
            workspace_id="ws-1",
            has_active_task=True,
            active_task_id="043-wasm",
            read_only=False,
        )
        native_allow = self.verifier.evaluate_native(req_deny, ctx_active)
        wasm_allow = self.verifier.evaluate_wasm(req_deny, ctx_active)
        self.assertEqual(native_allow.verdict, DecisionVerdict.ALLOW)
        self.assertEqual(native_allow.reason_code, 2002)
        self.assertEqual(wasm_allow.verdict, DecisionVerdict.ALLOW)
        self.assertEqual(wasm_allow.reason_code, 2002)

    def test_wasm_stdin_streaming_large_payload(self) -> None:
        """Tests that WASM runner handles large payloads via stdin streaming without E2BIG errors."""
        large_content = "x" * 200_000
        req = CapabilityRequest(
            action_type=ToolActionType.WRITE_FILE,
            raw_tool_name="write_to_file",
            target_resource="src/big_file.py",
            payload_json=f'{{"content":"{large_content}"}}',
        )
        ctx = EnforcementContext(
            workspace_id="ws-1",
            has_active_task=True,
            active_task_id="043-wasm",
            read_only=False,
        )
        dec = self.verifier.evaluate_wasm(req, ctx)
        self.assertEqual(dec.verdict, DecisionVerdict.ALLOW)

    def test_wasm_failure_fails_closed(self) -> None:
        """Verifies that when WASM execution fails or encounters error, it fails closed."""
        from unittest.mock import patch

        req = CapabilityRequest(
            action_type=ToolActionType.WRITE_FILE,
            raw_tool_name="write_to_file",
            target_resource="src/test.py",
        )
        ctx = EnforcementContext(
            workspace_id="ws-1",
            has_active_task=True,
            active_task_id="043-wasm",
            read_only=False,
        )
        # Force evaluate_wasm to raise an unexpected runtime exception
        with patch.object(self.verifier, "_cdll", None):
            with patch.object(
                self.verifier, "evaluate_wasm", side_effect=RuntimeError("V8 Engine Crashed")
            ):
                dec = self.verifier.evaluate(req, ctx)
                self.assertEqual(dec.verdict, DecisionVerdict.DENY)
                self.assertEqual(dec.reason_code, 4030)
                self.assertIn("failed closed", dec.reason.lower())


if __name__ == "__main__":
    unittest.main()
