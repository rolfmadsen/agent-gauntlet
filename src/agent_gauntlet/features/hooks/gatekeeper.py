"""Cooperative UX and Process Guardrail Hook Policy Engine for agent-gauntlet.

Ensures the agent is protected against unintended modifications to production source code
without an active task in tasks/, and blocks remote git publications and destructive operations.
NOTE: This engine serves as a cooperative agent process guardrail rather than an impenetrable OS boundary.
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
from agent_gauntlet.features.tasks import (
    has_active_task,
    is_task_active,
)

FORBIDDEN_COMMAND_PATTERNS = [
    r"\bgit(?:\$\{IFS\}|\s+).*?\bpush\b",
    r"\bgh(?:\$\{IFS\}|\s+).*?\bpr\s+create\b",
    r"\bgh(?:\$\{IFS\}|\s+).*?\brelease\s+create\b",
    r"\bgit(?:\$\{IFS\}|\s+).*?--(?:hard|merge)\b",
    r"\bgit(?:\$\{IFS\}|\s+).*?\bclean\b.*?-[a-zA-Z0-9]*f",
    r"\bgit(?:\$\{IFS\}|\s+).*?\bbranch\b.*?-[dD]\b",
    r"python[0-9.]*\s+.*?(?:subprocess|os\.system|exec|spawn).*?git.*?push",
]

SHELL_PROTECTED_PATH_PATTERNS = [
    r"(?:>|>>|\btee\b|\bdd\b\s+.*?of=)\s*['\"]?[^\s;&|]*(?:src|tests|\.agents|\.github)/",
    r"\b(?:rm|cp|mv|sed\s+-i|truncate|touch)\b.*?\b(?:src|tests|\.agents|\.github)(?:/|\b)",
    r"python[0-9.]*\s+.*?(?:open\(|Path\(|\.write|shutil\.|os\.remove).*?(?:src|tests|\.agents|\.github)",
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
    ".agents/agents.md",
}

SAFE_READONLY_TOOLS = {
    "view_file",
    "list_dir",
    "grep_search",
    "find_by_name",
    "read_url_content",
    "ask_question",
    "generate_image",
    "list_permissions",
}

# Backward-compatible alias
_is_active_task_content = is_task_active


class PolicyEngine:
    """Core domain safety policy engine evaluating typed CapabilityRequests."""

    def evaluate(
        self,
        request: CapabilityRequest,
        context: TrustedEnforcementContext,
    ) -> PolicyDecision:
        """Evaluates a CapabilityRequest against workspace safety invariants."""
        # 1. Command Execution Policy
        if (
            isinstance(request, CommandExecutionRequest)
            or request.capability_type == CapabilityType.EXECUTE_COMMAND
        ):
            command_line = (
                getattr(request, "command_line", "")
                or str(request.payload.get("CommandLine", "")).strip()
            )
            for pattern in FORBIDDEN_COMMAND_PATTERNS:
                if re.search(pattern, command_line, re.IGNORECASE):
                    return PolicyDecision(
                        allowed=False,
                        decision="deny",
                        verdict_code=GatekeeperVerdict.BLOCKED_FORBIDDEN_COMMAND,
                        reason=f"🛑 Forbidden Command: Destructive operation or remote publication via '{command_line}' is strictly prohibited.",
                        rule_id="NO_DESTRUCTIVE_OR_REMOTE_COMMAND",
                    )

            # Check if shell command modifies protected code or policies without an active task
            if not context.has_active_task:
                for shell_pattern in SHELL_PROTECTED_PATH_PATTERNS:
                    if re.search(shell_pattern, command_line, re.IGNORECASE):
                        return PolicyDecision(
                            allowed=False,
                            decision="deny",
                            verdict_code=GatekeeperVerdict.BLOCKED_NO_ACTIVE_TASK,
                            reason=(
                                f"🛑 Pre-Invocation Gate: Shell command '{command_line}' targets protected files in `src/`, `tests/`, `.agents/` or `.github/` "
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
        if (
            isinstance(request, FileWriteRequest)
            or request.capability_type == CapabilityType.WRITE_FILE
        ):
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

            target_path = (
                target_file if target_file.is_absolute() else (context.workspace_root / target_file)
            )
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
            parts = [p.lower() for p in rel_path.parts]

            # Allow safe metadata and task/doc files
            if rel_str in ALLOWED_METADATA_PATHS or (
                len(parts) > 0 and parts[0] in ("tasks", "docs", "scratch", "tools")
            ):
                return PolicyDecision(
                    allowed=True,
                    decision="allow",
                    verdict_code=GatekeeperVerdict.ALLOW,
                )

            # Protected paths requiring active task: src/, tests/, .agents/hooks.json, .github/
            is_protected = (len(parts) > 0 and parts[0] in ("src", "tests", ".github")) or (
                len(parts) > 0 and parts[0] == ".agents" and rel_str != ".agents/agents.md"
            )

            if is_protected and not context.has_active_task:
                return PolicyDecision(
                    allowed=False,
                    decision="deny",
                    verdict_code=GatekeeperVerdict.BLOCKED_NO_ACTIVE_TASK,
                    reason=(
                        "🛑 Pre-Invocation Gate: Der findes ingen aktiv eller godkendt task i `tasks/`. "
                        f"Opret eller aktivér venligst en task før '{rel_str}' ændres."
                    ),
                    rule_id="ACTIVE_TASK_REQUIRED",
                )

            return PolicyDecision(
                allowed=True,
                decision="allow",
                verdict_code=GatekeeperVerdict.ALLOW,
            )

        # 3. Read operations allowed
        if (
            isinstance(request, FileReadRequest)
            or request.capability_type == CapabilityType.READ_FILE
        ):
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
    elif tool_name in ("view_file", "list_dir", "grep_search", "find_by_name", "read_url_content"):
        raw_target = str(
            tool_input.get("AbsolutePath")
            or tool_input.get("SearchPath")
            or tool_input.get("SearchDirectory")
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
