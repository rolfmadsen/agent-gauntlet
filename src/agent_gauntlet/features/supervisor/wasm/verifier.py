"""WASM Policy Verifier and deterministic policy evaluator."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

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
    """Evaluates capability requests deterministically according to the gauntlet-policy-engine contract.

    Supports:
    1. Native Rust shared library (.so) via ctypes for microsecond execution.
    2. WebAssembly binary (.wasm) via Node.js V8 WebAssembly engine.
    3. In-process Python verification fallback when binary artifacts are absent.
    """

    POLICY_VERSION = "0.8.1"

    def __init__(
        self,
        component_bytes: bytes | None = None,
        expected_digest: str | None = None,
        wasm_path: Path | str | None = None,
        so_path: Path | str | None = None,
    ) -> None:
        self._loaded_digest: str = ""
        self._is_wasm_loaded: bool = False
        self._component_bytes: bytes | None = None
        self._cdll: ctypes.CDLL | None = None

        # Resolve artifact paths
        pkg_dir = Path(__file__).parent
        resolved_wasm = Path(wasm_path) if wasm_path else pkg_dir / "policy_engine.wasm"
        resolved_so = Path(so_path) if so_path else pkg_dir / "libpolicy_engine.so"
        self._wasm_path: Path = resolved_wasm
        self._runner_path: Path = pkg_dir / "wasm_runner.js"

        # 1. Load component bytes if explicitly supplied
        if component_bytes:
            if expected_digest:
                self.load_component(component_bytes, expected_digest)
            else:
                digest = f"sha256:{hashlib.sha256(component_bytes).hexdigest()}"
                self.load_component(component_bytes, digest)
        elif self._wasm_path.exists():
            data = self._wasm_path.read_bytes()
            actual_digest = f"sha256:{hashlib.sha256(data).hexdigest()}"
            if expected_digest and actual_digest != expected_digest:
                raise WasmDigestMismatchError(
                    f"WASM component digest mismatch: actual '{actual_digest}' != expected '{expected_digest}'"
                )
            self._component_bytes = data
            self._loaded_digest = actual_digest
            self._is_wasm_loaded = True

        # 2. Try initializing native ctypes CDLL if .so exists
        if resolved_so.exists():
            try:
                cdll = ctypes.CDLL(str(resolved_so))
                cdll.evaluate_json.argtypes = [
                    ctypes.c_char_p,
                    ctypes.c_size_t,
                    ctypes.c_char_p,
                    ctypes.c_size_t,
                    ctypes.POINTER(ctypes.c_size_t),
                ]
                cdll.evaluate_json.restype = ctypes.c_void_p
                cdll.dealloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
                cdll.dealloc.restype = None
                self._cdll = cdll
            except Exception:
                self._cdll = None

    @property
    def is_wasm_loaded(self) -> bool:
        """Returns True if a WebAssembly binary has been loaded and verified."""
        return self._is_wasm_loaded

    @property
    def is_native_loaded(self) -> bool:
        """Returns True if the native shared library (.so) has been bound via ctypes."""
        return self._cdll is not None

    @property
    def loaded_digest(self) -> str:
        """Returns the SHA-256 digest of the loaded component."""
        return self._loaded_digest

    def load_component(self, wasm_bytes: bytes, expected_digest: str) -> None:
        """Verifies the SHA-256 digest of the component binary and arms the verifier."""
        actual_digest = f"sha256:{hashlib.sha256(wasm_bytes).hexdigest()}"
        if actual_digest != expected_digest:
            raise WasmDigestMismatchError(
                f"WASM component digest mismatch: actual '{actual_digest}' != expected '{expected_digest}'"
            )
        self._component_bytes = wasm_bytes
        self._loaded_digest = actual_digest
        self._is_wasm_loaded = True

    def get_policy_version(self) -> str:
        """Returns the active policy schema version."""
        return self.POLICY_VERSION

    def evaluate_native(
        self,
        request: CapabilityRequest,
        context: EnforcementContext,
    ) -> PolicyDecision:
        """Evaluates policy request via compiled Rust native library using ctypes."""
        if self._cdll is None:
            raise RuntimeError("Native policy engine library (.so) is not loaded.")

        req_json = json.dumps(request.to_dict()).encode("utf-8")
        ctx_json = json.dumps(context.to_dict()).encode("utf-8")
        out_len = ctypes.c_size_t()

        ptr = self._cdll.evaluate_json(
            req_json, len(req_json), ctx_json, len(ctx_json), ctypes.byref(out_len)
        )
        if not ptr or out_len.value == 0:
            return PolicyDecision(
                verdict=DecisionVerdict.DENY,
                reason="Native policy evaluation returned null output.",
                reason_code=4030,
            )

        try:
            res_bytes = ctypes.string_at(ptr, out_len.value)
            res_dict = json.loads(res_bytes.decode("utf-8"))
            return PolicyDecision(
                verdict=DecisionVerdict(res_dict.get("verdict", "deny")),
                reason=str(res_dict.get("reason", "")),
                reason_code=int(res_dict.get("reason_code", 0)),
            )
        finally:
            self._cdll.dealloc(ptr, out_len.value)

    def evaluate_wasm(
        self,
        request: CapabilityRequest,
        context: EnforcementContext,
        target_wasm_path: Path | str | None = None,
    ) -> PolicyDecision:
        """Evaluates policy request via Node.js V8 WebAssembly engine executing policy_engine.wasm."""
        wasm_file: str = ""
        temp_file: Path | None = None

        if target_wasm_path:
            wasm_file = str(Path(target_wasm_path).resolve())
        elif self._wasm_path.exists():
            wasm_file = str(self._wasm_path.resolve())
        elif self._component_bytes:
            temp = tempfile.NamedTemporaryFile(suffix=".wasm", delete=False)
            temp.write(self._component_bytes)
            temp.flush()
            temp.close()
            temp_file = Path(temp.name)
            wasm_file = str(temp_file)
        else:
            raise RuntimeError("No WASM binary available for WebAssembly evaluation.")

        try:
            stdin_payload = json.dumps(
                {
                    "request": request.to_dict(),
                    "context": context.to_dict(),
                }
            )
            cmd = ["node", str(self._runner_path), wasm_file]
            result = subprocess.run(
                cmd,
                input=stdin_payload,
                capture_output=True,
                text=True,
                timeout=5.0,
                check=False,
            )
            if result.returncode != 0:
                return PolicyDecision(
                    verdict=DecisionVerdict.DENY,
                    reason=f"WASM runner execution failed: {result.stderr.strip()}",
                    reason_code=4030,
                )

            res_dict = json.loads(result.stdout.strip())
            return PolicyDecision(
                verdict=DecisionVerdict(res_dict.get("verdict", "deny")),
                reason=str(res_dict.get("reason", "")),
                reason_code=int(res_dict.get("reason_code", 0)),
            )
        finally:
            if temp_file and temp_file.exists():
                try:
                    os.unlink(str(temp_file))
                except OSError:
                    pass

    def evaluate(
        self,
        request: CapabilityRequest,
        context: EnforcementContext,
    ) -> PolicyDecision:
        """Deterministically evaluates a capability request against trusted context.

        Prefers native Rust execution (ctypes), falls back to WASM engine,
        or deterministic Python invariants.
        """
        # 1. Native execution if available
        if self._cdll is not None:
            return self.evaluate_native(request, context)

        # 2. WASM runner if loaded and available
        if self._is_wasm_loaded and self._runner_path.exists():
            try:
                return self.evaluate_wasm(request, context)
            except Exception as exc:
                import logging

                logging.getLogger(__name__).warning("WASM policy evaluation failed closed: %s", exc)
                return PolicyDecision(
                    verdict=DecisionVerdict.DENY,
                    reason=f"WASM policy evaluation failed closed: {exc}",
                    reason_code=4030,
                )

        # 3. Deterministic Python fallback
        return self._evaluate_fallback(request, context)

    def _evaluate_fallback(
        self,
        request: CapabilityRequest,
        context: EnforcementContext,
    ) -> PolicyDecision:
        """Fallback in-process evaluation preserving gauntlet policy invariants."""
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
