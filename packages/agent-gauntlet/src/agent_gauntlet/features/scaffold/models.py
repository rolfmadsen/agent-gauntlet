"""Data models for Project Scaffolding."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ScaffoldStatus(str, Enum):
    """Status of an individual scaffolded file or directory."""

    CREATED = "CREATED"
    SKIPPED = "SKIPPED"
    OVERWRITTEN = "OVERWRITTEN"


@dataclass(frozen=True)
class ScaffoldEntry:
    """Represents a single scaffolded path."""

    path: str
    status: ScaffoldStatus
    description: str


@dataclass
class ScaffoldResult:
    """Aggregated result of workspace scaffolding."""

    workspace: Path
    stack: str
    stacks: list[str] = field(default_factory=list)
    harness: str = "antigravity"
    entries: list[ScaffoldEntry] = field(default_factory=list)
    success: bool = True

    def to_dict(self) -> dict[str, object]:
        """Serialize result to dictionary."""
        effective_stacks = self.stacks if self.stacks else ([self.stack] if self.stack else [])
        return {
            "workspace": str(self.workspace),
            "stack": self.stack,
            "stacks": effective_stacks,
            "harness": self.harness,
            "success": self.success,
            "created": [e.path for e in self.entries if e.status == ScaffoldStatus.CREATED],
            "skipped": [e.path for e in self.entries if e.status == ScaffoldStatus.SKIPPED],
            "overwritten": [e.path for e in self.entries if e.status == ScaffoldStatus.OVERWRITTEN],
            "entries": [
                {"path": e.path, "status": e.status.value, "description": e.description}
                for e in self.entries
            ],
        }

