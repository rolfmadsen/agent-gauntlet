"""Antigravity IDE Hook Shim forwarding capability requests to the local supervisor IPC."""

from __future__ import annotations

import json
from typing import Any

from agent_gauntlet.features.supervisor.core.models import (
    CapabilityRequest,
    RpcMethod,
    RpcRequest,
    ToolActionType,
)
from agent_gauntlet.features.supervisor.core.seams import IpcTransportSeam


class AntigravityHookShim:
    """Ultra-low latency hook shim intercepting Antigravity IDE tool invocations."""

    def __init__(self, transport: IpcTransportSeam | None = None) -> None:
        self.transport = transport

    def normalize_payload(self, payload: dict[str, Any]) -> CapabilityRequest:
        """Translates raw Antigravity payload to a strongly-typed CapabilityRequest."""
        tool_name = ""
        args: dict[str, Any] = {}

        if "toolCall" in payload and isinstance(payload["toolCall"], dict):
            tool_name = str(payload["toolCall"].get("name", "")).strip()
            args = payload["toolCall"].get("args", {})
            if not isinstance(args, dict):
                args = {}
        elif "tool_name" in payload:
            tool_name = str(payload.get("tool_name", "")).strip()
            args = payload.get("tool_input", {})
            if not isinstance(args, dict):
                args = {}

        if tool_name == "run_command":
            cmd = str(args.get("CommandLine", "")).strip()
            return CapabilityRequest(
                action_type=ToolActionType.EXECUTE_COMMAND,
                raw_tool_name=tool_name,
                target_resource=cmd,
                payload_json=json.dumps(args),
            )

        if tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
            target_file = str(args.get("TargetFile", "")).strip()
            return CapabilityRequest(
                action_type=ToolActionType.WRITE_FILE,
                raw_tool_name=tool_name,
                target_resource=target_file,
                payload_json=json.dumps(args),
            )

        if tool_name in (
            "view_file",
            "list_dir",
            "grep_search",
            "find_by_name",
            "read_url_content",
        ):
            target_res = str(
                args.get("AbsolutePath")
                or args.get("SearchPath")
                or args.get("SearchDirectory")
                or args.get("DirectoryPath")
                or args.get("Url")
                or ""
            ).strip()
            return CapabilityRequest(
                action_type=ToolActionType.READ_FILE,
                raw_tool_name=tool_name,
                target_resource=target_res,
                payload_json=json.dumps(args),
            )

        return CapabilityRequest(
            action_type=ToolActionType.OTHER,
            raw_tool_name=tool_name,
            target_resource="",
            payload_json=json.dumps(args),
        )

    def handle_hook(
        self,
        payload: dict[str, Any],
        workspace_id: str = "default",
    ) -> dict[str, Any]:
        """Processes hook invocation by querying supervisor daemon over local IPC."""
        request = self.normalize_payload(payload)

        # Handle offline supervisor fallback
        if not self.transport:
            if request.action_type == ToolActionType.READ_FILE:
                return {
                    "decision": "allow",
                    "reason": "Supervisor IPC unavailable; safe read operation permitted.",
                }
            return {
                "decision": "deny",
                "reason": "Supervisor daemon is unavailable. Modifying operations are blocked fail-closed.",
            }

        try:
            rpc_req = RpcRequest(
                id="hook_eval",
                method=RpcMethod.EVALUATE_TOOL_CALL,
                params={
                    "workspace_id": workspace_id,
                    "request": request.to_dict(),
                },
            )
            rpc_res = self.transport.send_rpc(rpc_req)
            if not rpc_res.is_success or not rpc_res.result:
                return {
                    "decision": "deny",
                    "reason": f"Supervisor evaluation error: {rpc_res.error}",
                }

            decision_data = rpc_res.result.get("decision", {})
            return {
                "decision": decision_data.get("verdict", "deny"),
                "reason": decision_data.get("reason", "Policy decision"),
            }
        except Exception as exc:
            if request.action_type == ToolActionType.READ_FILE:
                return {
                    "decision": "allow",
                    "reason": f"Supervisor IPC communication error ({exc}); safe read permitted.",
                }
            return {
                "decision": "deny",
                "reason": f"Supervisor IPC failed: {exc}. Writes blocked fail-closed.",
            }
