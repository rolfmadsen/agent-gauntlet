"""Google Antigravity IDE adapter implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_gauntlet.features.adapters.antigravity.validator import AntigravityPluginValidator
from agent_gauntlet.features.adapters.models import (
    AdapterHookVerdict,
    AdapterValidationResult,
    NormalizedToolCall,
    ToolActionType,
)
from agent_gauntlet.features.hooks.gatekeeper import PolicyEngine, has_active_task
from agent_gauntlet.features.hooks.models import (
    CapabilityRequest,
    CommandExecutionRequest,
    FileReadRequest,
    FileWriteRequest,
    OtherCapabilityRequest,
    TrustedEnforcementContext,
)


class AntigravityAdapter:
    """Vertical slice adapter for Google Antigravity IDE."""

    name: str = "antigravity"

    def __init__(self) -> None:
        self.validator = AntigravityPluginValidator()
        self.policy_engine = PolicyEngine()

    def normalize_tool_call(self, payload: dict[str, Any] | str) -> NormalizedToolCall:
        """Translates raw Antigravity payloads into a NormalizedToolCall."""
        if isinstance(payload, str):
            try:
                data = json.loads(payload)
            except Exception:
                data = {}
        elif isinstance(payload, dict):
            data = payload
        else:
            data = {}

        tool_name = ""
        args: dict[str, Any] = {}

        # Canonical Antigravity PreToolUse payload format
        if "toolCall" in data and isinstance(data["toolCall"], dict):
            tool_name = str(data["toolCall"].get("name", "")).strip()
            args = data["toolCall"].get("args", {})
            if not isinstance(args, dict):
                args = {}
        # Legacy / flat hook payload format
        elif "tool_name" in data:
            tool_name = str(data.get("tool_name", "")).strip()
            args = data.get("tool_input", {})
            if not isinstance(args, dict):
                args = {}

        if tool_name == "run_command":
            cmd = str(args.get("CommandLine", "")).strip()
            return NormalizedToolCall(
                action_type=ToolActionType.EXECUTE_COMMAND,
                target_resource=cmd,
                raw_tool_name=tool_name,
                payload=args,
            )

        if tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
            target_file = str(args.get("TargetFile", "")).strip()
            return NormalizedToolCall(
                action_type=ToolActionType.WRITE_FILE,
                target_resource=target_file,
                raw_tool_name=tool_name,
                payload=args,
            )

        if tool_name in ("view_file", "list_dir", "grep_search", "read_url_content"):
            target_res = str(
                args.get("AbsolutePath")
                or args.get("SearchPath")
                or args.get("DirectoryPath")
                or args.get("Url")
                or ""
            ).strip()
            return NormalizedToolCall(
                action_type=ToolActionType.READ_FILE,
                target_resource=target_res,
                raw_tool_name=tool_name,
                payload=args,
            )

        return NormalizedToolCall(
            action_type=ToolActionType.OTHER,
            target_resource="",
            raw_tool_name=tool_name,
            payload=args,
        )

    def to_capability_request(self, payload: dict[str, Any] | str) -> CapabilityRequest:
        """Translates an Antigravity tool payload into a typed CapabilityRequest."""
        normalized = self.normalize_tool_call(payload)
        if normalized.action_type == ToolActionType.EXECUTE_COMMAND:
            return CommandExecutionRequest(
                command_line=normalized.target_resource,
                raw_tool_name=normalized.raw_tool_name,
                payload=normalized.payload,
            )
        if normalized.action_type == ToolActionType.WRITE_FILE:
            return FileWriteRequest(
                target_file=normalized.target_resource,
                raw_tool_name=normalized.raw_tool_name,
                payload=normalized.payload,
            )
        if normalized.action_type == ToolActionType.READ_FILE:
            return FileReadRequest(
                target_path=normalized.target_resource,
                raw_tool_name=normalized.raw_tool_name,
                payload=normalized.payload,
            )
        return OtherCapabilityRequest(
            tool_name=normalized.raw_tool_name,
            payload=normalized.payload,
        )

    def evaluate_invocation(
        self,
        workspace: Path,
        payload: dict[str, Any] | str,
    ) -> AdapterHookVerdict:
        """Evaluates an Antigravity tool invocation payload against PolicyEngine invariants."""
        request = self.to_capability_request(payload)
        context = TrustedEnforcementContext(
            workspace_root=workspace,
            has_active_task=has_active_task(workspace),
            harness_origin="antigravity",
        )
        decision = self.policy_engine.evaluate(request, context)
        return AdapterHookVerdict(
            allowed=decision.allowed,
            decision=decision.decision,
            reason=decision.reason,
        )

    def validate_plugin(self, plugin_dir: Path) -> AdapterValidationResult:
        """Mechanically validates an Antigravity plugin."""
        return self.validator.validate(plugin_dir)
