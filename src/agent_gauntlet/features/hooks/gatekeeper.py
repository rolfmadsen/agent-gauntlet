"""Surgical Pre-Invocation Hook Gatekeeper for agent-gauntlet.

Ensures the agent cannot modify production source code without an active task in tasks/,
and strictly prohibits remote git publications.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class GatekeeperVerdict(str, Enum):
    """Verdict codes for tool invocation evaluation."""

    ALLOW = "ALLOW"
    BLOCKED_NO_ACTIVE_TASK = "BLOCKED_NO_ACTIVE_TASK"
    BLOCKED_FORBIDDEN_COMMAND = "BLOCKED_FORBIDDEN_COMMAND"


@dataclass(frozen=True)
class HookResult:
    """Result of gatekeeper evaluation."""

    allowed: bool
    verdict_code: GatekeeperVerdict
    reason: str


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


def evaluate_tool_invocation(
    workspace: Path,
    tool_name: str,
    tool_input: dict[str, Any],
) -> HookResult:
    """Evaluate whether a tool invocation is allowed to proceed."""
    # 1. Run Command Guard: Check for forbidden remote commands
    if tool_name == "run_command":
        command_line = str(tool_input.get("CommandLine", "")).strip()
        for pattern in FORBIDDEN_COMMAND_PATTERNS:
            if re.search(pattern, command_line, re.IGNORECASE):
                return HookResult(
                    allowed=False,
                    verdict_code=GatekeeperVerdict.BLOCKED_FORBIDDEN_COMMAND,
                    reason=f"🛑 Forbidden Command: Remote publication via '{command_line}' is strictly prohibited. Git operations must remain local.",
                )
        return HookResult(allowed=True, verdict_code=GatekeeperVerdict.ALLOW, reason="")

    # 2. File Edit Guard: Check for edits to protected source directories
    if tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
        raw_target = str(tool_input.get("TargetFile", "")).strip()
        if not raw_target:
            return HookResult(allowed=True, verdict_code=GatekeeperVerdict.ALLOW, reason="")

        target_path = Path(raw_target).resolve()
        try:
            rel_path = target_path.relative_to(workspace.resolve())
        except ValueError:
            # File is outside workspace; let sandbox handle it
            return HookResult(allowed=True, verdict_code=GatekeeperVerdict.ALLOW, reason="")

        rel_str = str(rel_path).replace("\\", "/").lower()
        parts = rel_path.parts

        # Always allow editing metadata, tasks, docs, scratch, and config files
        if (
            rel_str in ALLOWED_METADATA_PATHS
            or (len(parts) > 0 and parts[0].lower() in ("tasks", "docs", ".agents", "scratch", "tools"))
        ):
            return HookResult(allowed=True, verdict_code=GatekeeperVerdict.ALLOW, reason="")

        # If editing src/ or tests/, require an active task in tasks/
        if len(parts) > 0 and parts[0].lower() in ("src", "tests"):
            if not has_active_task(workspace):
                return HookResult(
                    allowed=False,
                    verdict_code=GatekeeperVerdict.BLOCKED_NO_ACTIVE_TASK,
                    reason=(
                        "🛑 Pre-Invocation Gate: Der findes ingen aktiv eller godkendt task i `tasks/`. "
                        "Opret eller aktivér venligst `tasks/00X-<titel>.md` med godkendte acceptkriterier "
                        "før kildekoden i `src/` eller `tests/` ændres."
                    ),
                )

    # 3. All other tools (view_file, list_dir, grep_search, etc.) are allowed unconditionally
    return HookResult(allowed=True, verdict_code=GatekeeperVerdict.ALLOW, reason="")


def main_hook_entrypoint(argv: list[str] | None = None) -> int:
    """CLI entrypoint for Antigravity IDE PreInvocation hook."""
    workspace = Path(os.getcwd()).resolve()
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # If no json payload provided, fail open
        return 0

    tool_name = ""
    tool_input = {}
    if "toolCall" in payload and isinstance(payload["toolCall"], dict):
        tool_name = payload["toolCall"].get("name", "")
        tool_input = payload["toolCall"].get("args", {})
    else:
        tool_name = payload.get("tool_name", "")
        tool_input = payload.get("tool_input", {})

    result = evaluate_tool_invocation(workspace=workspace, tool_name=tool_name, tool_input=tool_input)
    if not result.allowed:
        sys.stderr.write(f"\n{result.reason}\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main_hook_entrypoint())
