"""Domain models for gauntlet execution layers and reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class LayerExecutionStatus(str, Enum):
    """Execution status of a verification layer."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    UNAVAILABLE = "UNAVAILABLE"
    TIMED_OUT = "TIMED_OUT"
    ERROR = "ERROR"


class LayerRequirement(str, Enum):
    """Enforcement requirement for a verification layer."""

    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"


@dataclass(frozen=True)
class LayerDefinition:
    """Definition of a single verification layer in the gauntlet."""

    name: str
    command: Sequence[str]
    optional: bool = False
    timeout_seconds: float = 60.0
    requirement: LayerRequirement = LayerRequirement.REQUIRED

    def __post_init__(self) -> None:
        if self.optional and self.requirement == LayerRequirement.REQUIRED:
            object.__setattr__(self, "requirement", LayerRequirement.OPTIONAL)
        elif not self.optional and self.requirement == LayerRequirement.OPTIONAL:
            object.__setattr__(self, "optional", True)


@dataclass(frozen=True)
class LayerResult:
    """Result of running a single verification layer."""

    name: str
    exit_code: int
    passed: bool
    output: str
    status: LayerExecutionStatus = LayerExecutionStatus.PASSED
    duration_seconds: float = 0.0
    requirement: LayerRequirement = LayerRequirement.REQUIRED


@dataclass(frozen=True)
class GauntletReport:
    """Consolidated execution report from all verification layers."""

    success: bool
    layers: list[LayerResult] = field(default_factory=list)
    total_duration_seconds: float = 0.0

