"""Cursor IDE adapter implementation for agent-gauntlet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_gauntlet.features.adapters.cursor.validator import CursorRulesValidator
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


class CursorAdapter:
    """Vertical slice adapter for Cursor IDE."""

    name: str = "cursor"

    def __init__(self) -> None:
        self.validator = CursorRulesValidator()
        self.policy_engine = PolicyEngine()

    def normalize_tool_call(self, payload: dict[str, Any] | str) -> NormalizedToolCall:
        """Translates raw Cursor payloads into a canonical NormalizedToolCall.

        Args:
            payload: JSON string or dictionary representing a tool invocation.

        Returns:
            NormalizedToolCall with standardized action type and target resource.
        """
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

        # 1. Canonical / composer format {"toolCall": {"name": ..., "args": ...}}
        if "toolCall" in data and isinstance(data["toolCall"], dict):
            tool_name = str(data["toolCall"].get("name", "")).strip()
            args = data["toolCall"].get("args", {})
            if not isinstance(args, dict):
                args = {}
        # 2. OpenAI / function format {"name": ..., "arguments" | "parameters": ...}
        elif "name" in data:
            tool_name = str(data.get("name", "")).strip()
            args = data.get("arguments") or data.get("parameters") or {}
            if not isinstance(args, dict):
                args = {}
        # 3. Flat hook format {"tool_name": ..., "tool_input": ...}
        elif "tool_name" in data:
            tool_name = str(data.get("tool_name", "")).strip()
            args = data.get("tool_input", {})
            if not isinstance(args, dict):
                args = {}
        # 4. Action format {"action": ..., "params": ...}
        elif "action" in data:
            tool_name = str(data.get("action", "")).strip()
            args = data.get("params", {})
            if not isinstance(args, dict):
                args = {}

        # Check for command execution tools
        if tool_name in (
            "run_terminal_command",
            "run_command",
            "terminal",
            "bash",
            "execute_command",
            "command",
        ):
            cmd = str(
                args.get("command") or args.get("CommandLine") or args.get("cmd") or ""
            ).strip()
            return NormalizedToolCall(
                action_type=ToolActionType.EXECUTE_COMMAND,
                target_resource=cmd,
                raw_tool_name=tool_name,
                payload=args,
            )

        # Check for file write tools
        if tool_name in (
            "write_file",
            "edit_file",
            "create_file",
            "update_file",
            "write_to_file",
            "replace_file_content",
            "multi_replace_file_content",
        ):
            target_file = str(
                args.get("path")
                or args.get("target_file")
                or args.get("file_path")
                or args.get("TargetFile")
                or args.get("filePath")
                or ""
            ).strip()
            return NormalizedToolCall(
                action_type=ToolActionType.WRITE_FILE,
                target_resource=target_file,
                raw_tool_name=tool_name,
                payload=args,
            )

        # Check for file read tools
        if tool_name in (
            "read_file",
            "view_file",
            "list_dir",
            "grep_search",
            "file_search",
            "read_dir",
            "find_by_name",
        ):
            target_res = str(
                args.get("path")
                or args.get("target_file")
                or args.get("target_path")
                or args.get("AbsolutePath")
                or args.get("SearchPath")
                or args.get("DirectoryPath")
                or args.get("directory")
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
        """Translates a Cursor tool payload into a typed CapabilityRequest.

        Args:
            payload: Raw JSON string or dictionary representing a tool invocation.

        Returns:
            Typed CapabilityRequest domain object.
        """
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
        """Evaluates a Cursor tool invocation payload against PolicyEngine invariants.

        Args:
            workspace: Target workspace root path.
            payload: Tool invocation payload.

        Returns:
            AdapterHookVerdict indicating whether the operation is allowed.
        """
        request = self.to_capability_request(payload)
        context = TrustedEnforcementContext(
            workspace_root=workspace,
            has_active_task=has_active_task(workspace),
            harness_origin="cursor",
        )
        decision = self.policy_engine.evaluate(request, context)
        return AdapterHookVerdict(
            allowed=decision.allowed,
            decision=decision.decision,
            reason=decision.reason,
        )

    def validate_plugin(self, plugin_dir: Path) -> AdapterValidationResult:
        """Mechanically validates Cursor rules and configuration.

        Args:
            plugin_dir: Workspace or rule directory.

        Returns:
            AdapterValidationResult containing issues and validity status.
        """
        return self.validator.validate(plugin_dir)
