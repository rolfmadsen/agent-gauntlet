"""WASM Policy Verifier and deterministic policy evaluator."""

from __future__ import annotations

import hashlib

from agent_gauntlet.features.supervisor.core.models import (
    CapabilityRequest,
    DecisionVerdict,
    EnforcementContext,
    PolicyDecision,
    ToolActionType,
)


class WasmDigestMismatchError(Exception):
    """Raised when a WASM component binary fails SHA-256 digest verification."""


class WasmPolicyVerifier:
    """Evaluates capability requests deterministically according to the gauntlet-policy-engine contract."""

    POLICY_VERSION = "0.5.0"

    def __init__(
        self, component_bytes: bytes | None = None, expected_digest: str | None = None
    ) -> None:
        self._loaded_digest: str = ""
        self._is_wasm_loaded: bool = False
        if component_bytes and expected_digest:
            self.load_component(component_bytes, expected_digest)

    def load_component(self, wasm_bytes: bytes, expected_digest: str) -> None:
        """Verifies the SHA-256 digest of the component binary and arms the verifier."""
        actual_digest = f"sha256:{hashlib.sha256(wasm_bytes).hexdigest()}"
        if actual_digest != expected_digest:
            raise WasmDigestMismatchError(
                f"WASM component digest mismatch: actual '{actual_digest}' != expected '{expected_digest}'"
            )
        self._loaded_digest = actual_digest
        self._is_wasm_loaded = True

    def get_policy_version(self) -> str:
        """Returns the active policy schema version."""
        return self.POLICY_VERSION

    def evaluate(
        self,
        request: CapabilityRequest,
        context: EnforcementContext,
    ) -> PolicyDecision:
        """Deterministically evaluates a capability request against the trusted context.

        Invariants:
        1. When read_only is True: Deny any write or mutating execution request.
        2. Read operations (READ_FILE) are unconditionally ALLOWED.
        3. Write operations (WRITE_FILE) to documentation/tasks/spec are unconditionally ALLOWED.
        4. Write operations (WRITE_FILE) to src/ or tests/ REQUIRE an active task.
        5. Execution operations (EXECUTE_COMMAND) with dangerous/destructive commands REQUIRE an active task.
        """
        # Invariant 1: Global read-only enforcement
        if context.read_only:
            if request.action_type in (ToolActionType.WRITE_FILE, ToolActionType.EXECUTE_COMMAND):
                return PolicyDecision(
                    verdict=DecisionVerdict.DENY,
                    reason="Workspace is in read-only mode; state mutation is prohibited.",
                    reason_code=4030,
                )

        # Invariant 2: Pure read operations
        if request.action_type == ToolActionType.READ_FILE:
            return PolicyDecision(
                verdict=DecisionVerdict.ALLOW,
                reason="Read operations are unrestricted.",
                reason_code=2000,
            )

        # Invariant 3 & 4: File write operations
        if request.action_type == ToolActionType.WRITE_FILE:
            target = request.target_resource.replace("\\", "/").strip()

            # Tasks, spec, context, and documentation can always be written/refined
            if (
                target.startswith("tasks/")
                or target in ("spec.md", "CONTEXT.md", "CODING_STANDARDS.md", "README.md")
                or target.startswith("docs/")
            ):
                return PolicyDecision(
                    verdict=DecisionVerdict.ALLOW,
                    reason="Writing task definitions or domain documentation is permitted.",
                    reason_code=2001,
                )

            # Code/test mutations require an active task
            if (
                target.startswith("src/")
                or target.startswith("tests/")
                or target.startswith("packages/")
            ):
                if not context.has_active_task:
                    return PolicyDecision(
                        verdict=DecisionVerdict.DENY,
                        reason="Writing to production code without active task is prohibited.",
                        reason_code=4031,
                    )
                return PolicyDecision(
                    verdict=DecisionVerdict.ALLOW,
                    reason=f"Writing to code permitted under active task '{context.active_task_id}'.",
                    reason_code=2002,
                )

            # Default for other write operations
            if not context.has_active_task:
                return PolicyDecision(
                    verdict=DecisionVerdict.DENY,
                    reason="Mutating repository files without an active task is prohibited.",
                    reason_code=4032,
                )
            return PolicyDecision(
                verdict=DecisionVerdict.ALLOW,
                reason="Write operation permitted under active task.",
                reason_code=2003,
            )

        # Invariant 5: Command execution
        if request.action_type == ToolActionType.EXECUTE_COMMAND:
            cmd = request.target_resource.strip()
            # Safe read-only commands
            safe_prefixes = (
                "git status",
                "git diff",
                "git log",
                "ls",
                "pwd",
                "echo",
                "which",
                "pytest",
                "python -m unittest",
                "python3 -m unittest",
                "cargo check",
                "cargo test",
                "ruff check",
                "pyright",
                "agent-gauntlet verify",
                "sh tools/gauntlet.sh",
            )
            if any(cmd.startswith(p) for p in safe_prefixes):
                return PolicyDecision(
                    verdict=DecisionVerdict.ALLOW,
                    reason="Read-only or verification command is permitted.",
                    reason_code=2004,
                )

            # Mutating commands require active task
            if not context.has_active_task:
                return PolicyDecision(
                    verdict=DecisionVerdict.DENY,
                    reason="Executing modifying commands without an active task is prohibited.",
                    reason_code=4033,
                )
            return PolicyDecision(
                verdict=DecisionVerdict.ALLOW,
                reason="Command execution permitted under active task.",
                reason_code=2005,
            )

        # Other / unknown tool actions
        return PolicyDecision(
            verdict=DecisionVerdict.ALLOW,
            reason="Other capability request permitted by default.",
            reason_code=2000,
        )
