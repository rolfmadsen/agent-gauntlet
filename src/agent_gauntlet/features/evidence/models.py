"""Domain models for HMAC-signed cryptographic evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class CheckSummary:
    """Summary of a single verification check."""

    name: str
    passed: bool
    exit_code: int
    duration_seconds: float = 0.0


@dataclass(frozen=True)
class EvidenceRecord:
    """Immutable evidence record representing a gauntlet verification run."""

    task_id: str
    status: str
    source_tree_hash: str
    task_title: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    unresolved_criteria: list[str] = field(default_factory=list)
    checks: list[CheckSummary] = field(default_factory=list)
    timestamp: float = 0.0
    signature: str | None = None
