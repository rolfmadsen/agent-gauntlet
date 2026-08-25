"""Data models and discriminated CapabilityRequest types for PolicyEngine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class CapabilityType(str, Enum):
    """Categorization of agent capability requests."""

    EXECUTE_COMMAND = "EXECUTE_COMMAND"
    WRITE_FILE = "WRITE_FILE"
    READ_FILE = "READ_FILE"
    OTHER = "OTHER"


class GatekeeperVerdict(str, Enum):
    """Verdict codes for policy evaluation."""

    ALLOW = "ALLOW"
    BLOCKED_NO_ACTIVE_TASK = "BLOCKED_NO_ACTIVE_TASK"
    BLOCKED_FORBIDDEN_COMMAND = "BLOCKED_FORBIDDEN_COMMAND"
    BLOCKED_MALFORMED_INPUT = "BLOCKED_MALFORMED_INPUT"


@dataclass(frozen=True)
class CapabilityRequest:
    """Base discriminated capability request."""

    capability_type: CapabilityType
    raw_tool_name: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandExecutionRequest(CapabilityRequest):
    """Request to execute a shell or CLI command."""

    command_line: str = ""
    bypass_sandbox: bool = False

    def __init__(
        self,
        command_line: str,
        bypass_sandbox: bool = False,
        raw_tool_name: str = "run_command",
        payload: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "capability_type", CapabilityType.EXECUTE_COMMAND)
        object.__setattr__(self, "command_line", command_line)
        object.__setattr__(self, "bypass_sandbox", bypass_sandbox)
        object.__setattr__(self, "raw_tool_name", raw_tool_name)
        object.__setattr__(self, "payload", payload or {})


@dataclass(frozen=True)
class FileWriteRequest(CapabilityRequest):
    """Request to create, overwrite, or edit a workspace file."""

    target_file: Path = field(default_factory=Path)
    allow_multiple: bool = False

    def __init__(
        self,
        target_file: Path | str,
        allow_multiple: bool = False,
        raw_tool_name: str = "write_to_file",
        payload: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "capability_type", CapabilityType.WRITE_FILE)
        object.__setattr__(self, "target_file", Path(target_file))
        object.__setattr__(self, "allow_multiple", allow_multiple)
        object.__setattr__(self, "raw_tool_name", raw_tool_name)
        object.__setattr__(self, "payload", payload or {})


@dataclass(frozen=True)
class FileReadRequest(CapabilityRequest):
    """Request to inspect or search files without modification."""

    target_path: Path = field(default_factory=Path)

    def __init__(
        self,
        target_path: Path | str,
        raw_tool_name: str = "view_file",
        payload: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "capability_type", CapabilityType.READ_FILE)
        object.__setattr__(self, "target_path", Path(target_path))
        object.__setattr__(self, "raw_tool_name", raw_tool_name)
        object.__setattr__(self, "payload", payload or {})


@dataclass(frozen=True)
class OtherCapabilityRequest(CapabilityRequest):
    """Request for unclassified or auxiliary tools."""

    def __init__(self, tool_name: str = "other", payload: dict[str, Any] | None = None) -> None:
        object.__setattr__(self, "capability_type", CapabilityType.OTHER)
        object.__setattr__(self, "raw_tool_name", tool_name)
        object.__setattr__(self, "payload", payload or {})


@dataclass(frozen=True)
class TrustedEnforcementContext:
    """Immutable environment context assembled by trusted adapter."""

    workspace_root: Path
    has_active_task: bool = False
    harness_origin: str = "antigravity"
    is_interactive: bool = True


@dataclass(frozen=True)
class PolicyDecision:
    """Evaluation verdict produced by PolicyEngine."""

    allowed: bool
    decision: str
    verdict_code: GatekeeperVerdict
    reason: str = ""
    rule_id: str = ""


# Backward-compatible alias
HookResult = PolicyDecision
