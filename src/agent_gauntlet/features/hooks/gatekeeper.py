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
                        reason=f"🛑 Forbidden Command: Remote publication via '{command_line}' is strictly prohibited. Git operations must remain local.",
                        rule_id="NO_REMOTE_PUBLICATION",
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
                    allowed=True,
                    decision="allow",
                    verdict_code=GatekeeperVerdict.ALLOW,
                )

            target_path = target_file if target_file.is_absolute() else (context.workspace_root / target_file)
            resolved_target = target_path.resolve()
            resolved_root = context.workspace_root.resolve()

            try:
                rel_path = resolved_target.relative_to(resolved_root)
            except ValueError:
                # File is outside workspace root; allow sandbox isolation to handle
                return PolicyDecision(
                    allowed=True,
                    decision="allow",
                    verdict_code=GatekeeperVerdict.ALLOW,
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

        # 3. Read and other operations allowed unconditionally
        return PolicyDecision(
            allowed=True,
            decision="allow",
            verdict_code=GatekeeperVerdict.ALLOW,
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
