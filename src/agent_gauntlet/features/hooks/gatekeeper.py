"""Surgical Pre-Invocation Hook Policy Engine for agent-gauntlet.

Ensures the agent cannot modify production source code without an active task in tasks/,
and strictly prohibits remote git publications and destructive operations.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from agent_gauntlet.features.hooks.models import (
    CapabilityRequest,
    CapabilityType,
    CommandExecutionRequest,
    FileReadRequest,
    FileWriteRequest,
    GatekeeperVerdict,
    HookResult,
    OtherCapabilityRequest,
    PolicyDecision,
    TrustedEnforcementContext,
)

FORBIDDEN_COMMAND_PATTERNS = [
    r"\bgit\s+push\b",
    r"\bgh\s+pr\s+create\b",
    r"\bgh\s+release\s+create\b",
    r"\bgit\s+reset\s+--(hard|merge)\b",
    r"\bgit\s+clean\s+-[a-zA-Z]*f",
    r"\bgit\s+branch\s+-D\b",
]

SHELL_PROTECTED_PATH_PATTERNS = [
    r"(?:>|>>|\btee\b)\s+[^\s;&|]*(?:src|tests)/",
    r"\b(?:rm|cp|mv|sed\s+-i|truncate|touch)\b.*?\b(?:src|tests)(?:/|\b)",
]

ALLOWED_METADATA_PATHS = {
    "claude.md",
    "context.md",
    "evidence.json",
    "evidence.md",
    "gauntlet.toml",
    "gauntlet.json",
    "pyproject.toml",
    "readme.md",
    "roadmap.md",
    "spec.md",
    "verification-report.json",
}

SAFE_READONLY_TOOLS = {
    "view_file",
    "list_dir",
    "grep_search",
    "read_url_content",
    "ask_question",
    "generate_image",
}


def parse_task_status(content: str) -> str:
    """Extract task status from task markdown content."""
    status_match = re.search(r"\*\*Status\*\*:\s*`?([A-Za-z_-]+)`?", content, re.IGNORECASE)
    if status_match:
        return status_match.group(1).upper()

    header_match = re.search(r"\bStatus:\s*`?([A-Za-z_-]+)`?", content, re.IGNORECASE)
    if header_match:
        return header_match.group(1).upper()

    return ""


def is_task_active(content: str) -> bool:
    """Check if task file content represents an active/approved task."""
    status = parse_task_status(content)
    if status and status in ("DONE", "COMPLETED", "DEPRECATED", "SUPERSEDED"):
        return False
    # Check for presence of acceptance criteria section
    has_criteria = "acceptance criteria" in content.lower() or "- [" in content
    return has_criteria


# Backward-compatible alias
_is_active_task_content = is_task_active


def has_active_task(workspace: Path) -> bool:
    """Determine whether the workspace has at least one active task in tasks/."""
    tasks_dir = workspace / "tasks"
    if not tasks_dir.is_dir():
        return False

    for task_path in tasks_dir.glob("*.md"):
        try:
            content = task_path.read_text(encoding="utf-8")
            if is_task_active(content):
                return True
        except (OSError, UnicodeDecodeError):
            continue

    return False


class PolicyEngine:
    """Core domain safety policy engine evaluating typed CapabilityRequests."""

    def evaluate(
        self,
        request: CapabilityRequest,
        context: TrustedEnforcementContext,
    ) -> PolicyDecision:
        """Evaluates a CapabilityRequest against workspace safety invariants."""
        # 1. Command Execution Policy
        if isinstance(request, CommandExecutionRequest) or request.capability_type == CapabilityType.EXECUTE_COMMAND:
            command_line = getattr(request, "command_line", "") or str(request.payload.get("CommandLine", "")).strip()
            for pattern in FORBIDDEN_COMMAND_PATTERNS:
                if re.search(pattern, command_line, re.IGNORECASE):
                    return PolicyDecision(
                        allowed=False,
                        decision="deny",
                        verdict_code=GatekeeperVerdict.BLOCKED_FORBIDDEN_COMMAND,
                        reason=f"🛑 Forbidden Command: Destructive operation or remote publication via '{command_line}' is strictly prohibited.",
                        rule_id="NO_DESTRUCTIVE_OR_REMOTE_COMMAND",
                    )

            # Check if shell command modifies protected code without an active task
            if not context.has_active_task:
                for shell_pattern in SHELL_PROTECTED_PATH_PATTERNS:
                    if re.search(shell_pattern, command_line, re.IGNORECASE):
                        return PolicyDecision(
                            allowed=False,
                            decision="deny",
                            verdict_code=GatekeeperVerdict.BLOCKED_NO_ACTIVE_TASK,
                            reason=(
                                f"🛑 Pre-Invocation Gate: Shell command '{command_line}' targets protected source files in `src/` or `tests/` "
                                "without an active task in `tasks/`. Opret eller aktivér venligst en task først."
                            ),
                            rule_id="ACTIVE_TASK_REQUIRED",
                        )

            return PolicyDecision(
                allowed=True,
                decision="allow",
                verdict_code=GatekeeperVerdict.ALLOW,
                reason="",
                rule_id="ALLOW_LOCAL_COMMAND",
            )

        # 2. File Write Policy
        if isinstance(request, FileWriteRequest) or request.capability_type == CapabilityType.WRITE_FILE:
            target_file = getattr(request, "target_file", None)
            if target_file is None:
                raw_target = str(request.payload.get("TargetFile", "")).strip()
                target_file = Path(raw_target) if raw_target else None

            if not target_file or not str(target_file).strip():
                return PolicyDecision(
                    allowed=False,
                    decision="deny",
                    verdict_code=GatekeeperVerdict.BLOCKED_MALFORMED_INPUT,
                    reason="🛑 Pre-Invocation Gate: Empty target file path provided for file write operation.",
                )

            target_path = target_file if target_file.is_absolute() else (context.workspace_root / target_file)
            resolved_target = target_path.resolve()
            resolved_root = context.workspace_root.resolve()

            try:
                rel_path = resolved_target.relative_to(resolved_root)
            except ValueError:
                # File is outside workspace root -> Strict fail-closed workspace escape prevention
                return PolicyDecision(
                    allowed=False,
                    decision="deny",
                    verdict_code=GatekeeperVerdict.BLOCKED_FORBIDDEN_COMMAND,
                    reason=f"🛑 Workspace Escape: File write target '{resolved_target}' is outside workspace root '{resolved_root}'.",
                    rule_id="WORKSPACE_ESCAPE_PROHIBITED",
                )

            rel_str = str(rel_path).replace("\\", "/").lower()
            parts = rel_path.parts

            # Always allow editing metadata, tasks, docs, scratch, tools, and config files
            if (
                rel_str in ALLOWED_METADATA_PATHS
                or (len(parts) > 0 and parts[0].lower() in ("tasks", "docs", ".agents", "scratch", "tools"))
            ):
                return PolicyDecision(
                    allowed=True,
                    decision="allow",
                    verdict_code=GatekeeperVerdict.ALLOW,
                )

            # Protected source code / tests require an active task
            if len(parts) > 0 and parts[0].lower() in ("src", "tests"):
                if not context.has_active_task:
                    return PolicyDecision(
                        allowed=False,
                        decision="deny",
                        verdict_code=GatekeeperVerdict.BLOCKED_NO_ACTIVE_TASK,
                        reason=(
                            "🛑 Pre-Invocation Gate: Der findes ingen aktiv eller godkendt task i `tasks/`. "
                            "Opret eller aktivér venligst `tasks/00X-<titel>.md` med godkendte acceptkriterier "
                            "før kildekoden i `src/` eller `tests/` ændres."
                        ),
                        rule_id="ACTIVE_TASK_REQUIRED",
                    )

            return PolicyDecision(
                allowed=True,
                decision="allow",
                verdict_code=GatekeeperVerdict.ALLOW,
            )

        # 3. Read operations allowed
        if isinstance(request, FileReadRequest) or request.capability_type == CapabilityType.READ_FILE:
            return PolicyDecision(
                allowed=True,
                decision="allow",
                verdict_code=GatekeeperVerdict.ALLOW,
            )

        # 4. Recognized safe tools allowed
        tool_name = getattr(request, "raw_tool_name", "") or getattr(request, "tool_name", "")
        if tool_name in SAFE_READONLY_TOOLS:
            return PolicyDecision(
                allowed=True,
                decision="allow",
                verdict_code=GatekeeperVerdict.ALLOW,
            )

        # 5. Deny-by-default on unrecognized tools or malformed requests
        return PolicyDecision(
            allowed=False,
            decision="deny",
            verdict_code=GatekeeperVerdict.BLOCKED_MALFORMED_INPUT,
            reason=f"🛑 Pre-Invocation Gate: Unrecognized or unclassified tool capability '{tool_name}'. Deny-by-default enforced.",
            rule_id="FAIL_CLOSED_DENY_UNKNOWN",
        )


def evaluate_tool_invocation(
    workspace: Path,
    tool_name: str,
    tool_input: dict[str, Any],
) -> HookResult:
    """Backward-compatible helper evaluating raw tool invocation via PolicyEngine."""
    engine = PolicyEngine()
    active = has_active_task(workspace)
    context = TrustedEnforcementContext(
        workspace_root=workspace,
        has_active_task=active,
        harness_origin="legacy",
    )

    if tool_name == "run_command":
        cmd = str(tool_input.get("CommandLine", "")).strip()
        req: CapabilityRequest = CommandExecutionRequest(command_line=cmd, payload=tool_input)
    elif tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
        raw_target = str(tool_input.get("TargetFile", "")).strip()
        req = FileWriteRequest(target_file=raw_target, raw_tool_name=tool_name, payload=tool_input)
    elif tool_name in ("view_file", "list_dir", "grep_search", "read_url_content"):
        raw_target = str(
            tool_input.get("AbsolutePath")
            or tool_input.get("SearchPath")
            or tool_input.get("DirectoryPath")
            or tool_input.get("Url")
            or ""
        ).strip()
        req = FileReadRequest(target_path=raw_target, raw_tool_name=tool_name, payload=tool_input)
    else:
        req = OtherCapabilityRequest(tool_name=tool_name, payload=tool_input)

    return engine.evaluate(req, context)


def main_hook_entrypoint(argv: list[str] | None = None) -> int:
    """CLI entrypoint for Antigravity IDE PreInvocation hook."""
    from agent_gauntlet.features.adapters.antigravity.hook import main_hook_entrypoint as _hook_main
    return _hook_main(argv)


if __name__ == "__main__":
    sys.exit(main_hook_entrypoint())
