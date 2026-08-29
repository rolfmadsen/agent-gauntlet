"""Domain models and enum definitions for Task Packages and Task Contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(str, Enum):
    """Lifecycle status of a task specification in tasks/."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    IN_PROGRESS = "IN_PROGRESS"
    WIP = "WIP"
    TODO = "TODO"
    REOPENED = "REOPENED"
    DONE = "DONE"
    COMPLETED = "COMPLETED"
    DEPRECATED = "DEPRECATED"
    SUPERSEDED = "SUPERSEDED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_string(cls, raw: str) -> TaskStatus:
        """Parse status string into normalized TaskStatus."""
        clean = raw.strip().upper().replace("-", "_")
        for member in cls:
            if member.value == clean:
                return member
        return cls.UNKNOWN


# Allowed statuses that grant active work permission
ALLOWED_ACTIVE_STATUSES = {
    TaskStatus.ACTIVE,
    TaskStatus.IN_PROGRESS,
    TaskStatus.WIP,
    TaskStatus.TODO,
    TaskStatus.REOPENED,
}


@dataclass(frozen=True)
class TaskPackageInfo:
    """Parsed metadata and criteria for a task package."""

    task_id: str
    title: str = ""
    status: TaskStatus = TaskStatus.UNKNOWN
    acceptance_criteria: list[str] = field(default_factory=list)
    unresolved_criteria: list[str] = field(default_factory=list)
    must_not: list[str] = field(default_factory=list)
