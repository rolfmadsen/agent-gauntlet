"""Domain models for gauntlet execution layers and reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class LayerDefinition:
    """Definition of a single verification layer in the gauntlet."""

    name: str
    command: Sequence[str]
    optional: bool = False
    timeout_seconds: float = 60.0


@dataclass(frozen=True)
class LayerResult:
    """Result of running a single verification layer."""

    name: str
    exit_code: int
    passed: bool
    output: str
    duration_seconds: float = 0.0


@dataclass(frozen=True)
class GauntletReport:
    """Consolidated execution report from all verification layers."""

    success: bool
    layers: list[LayerResult] = field(default_factory=list)
    total_duration_seconds: float = 0.0
