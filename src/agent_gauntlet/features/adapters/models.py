"""Data models for harness adapters and normalized tool calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from pathlib import Path


class ToolActionType(str, Enum):
    """Categorization of agent tool operations."""

    EXECUTE_COMMAND = "EXECUTE_COMMAND"
    WRITE_FILE = "WRITE_FILE"
    READ_FILE = "READ_FILE"
    OTHER = "OTHER"


@dataclass(frozen=True)
class NormalizedToolCall:
    """Canonical representation of an agent action across different harnesses."""

    action_type: ToolActionType
    target_resource: str
    raw_tool_name: str
    payload: dict[str, Any] = field(default_factory=dict)


class ValidationSeverity(str, Enum):
    """Severity of a plugin validation finding."""

    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class ValidationIssue:
    """A specific issue encountered during mechanical plugin validation."""

    severity: ValidationSeverity
    path: str
    message: str


@dataclass(frozen=True)
class AdapterValidationResult:
    """Result of mechanical plugin and manifest validation."""

    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)


@dataclass(frozen=True)
class AdapterHookVerdict:
    """Verdict returned by adapter invocation evaluation."""

    allowed: bool
    decision: str
    reason: str = ""


class HarnessAdapterProtocol(Protocol):
    """Structural protocol defining the interface required of all harness adapters."""

    name: str

    def normalize_tool_call(self, payload: dict[str, Any] | str) -> NormalizedToolCall:
        ...

    def evaluate_invocation(
        self,
        workspace: Path,
        payload: dict[str, Any] | str,
    ) -> AdapterHookVerdict:
        ...

    def validate_plugin(self, plugin_dir: Path) -> AdapterValidationResult:
        ...
