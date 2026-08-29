"""Task contract resolver and criteria extractor for verification workflows."""

from __future__ import annotations

from pathlib import Path

from agent_gauntlet.features.evidence.models import TaskContract
from agent_gauntlet.features.tasks import resolve_task_contract

__all__ = ["resolve_task_contract", "build_task_contract"]


def build_task_contract(
    workspace: Path, explicit_task_id: str = "", task_digest: str = ""
) -> TaskContract:
    """Builds a TaskContract model for the active or explicit task in workspace."""
    task_id, task_title, acceptance_criteria, unresolved_criteria = resolve_task_contract(
        workspace, explicit_task_id
    )
    return TaskContract(
        task_id=task_id,
        task_title=task_title,
        task_digest=task_digest,
        acceptance_criteria=acceptance_criteria,
        unresolved_criteria=unresolved_criteria,
    )
