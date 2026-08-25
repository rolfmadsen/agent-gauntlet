"""Task contract resolver and criteria extractor for verification workflows."""

from __future__ import annotations

from pathlib import Path

from agent_gauntlet.features.evidence.models import TaskContract
from agent_gauntlet.features.hooks.gatekeeper import is_task_active


def resolve_task_contract(
    workspace: Path, explicit_task_id: str = ""
) -> tuple[str, str, list[str], list[str]]:
    """
    Finds and parses task contract from tasks/.
    Returns (task_id, task_title, acceptance_criteria, unresolved_criteria).
    """
    tasks_dir = workspace / "tasks"
    if not tasks_dir.is_dir():
        return explicit_task_id or "default-run", "", [], []

    target_file: Path | None = None

    if explicit_task_id and explicit_task_id != "gauntlet-run":
        for candidate in sorted(tasks_dir.glob("*.md")):
            if (
                candidate.stem == explicit_task_id
                or candidate.name == explicit_task_id
                or candidate.name.startswith(f"{explicit_task_id}-")
                or candidate.stem.startswith(explicit_task_id)
            ):
                target_file = candidate
                break

    if not target_file:
        for candidate in sorted(tasks_dir.glob("*.md")):
            try:
                content = candidate.read_text(encoding="utf-8")
                if is_task_active(content):
                    target_file = candidate
                    break
            except Exception:
                continue

    if not target_file:
        return explicit_task_id or "default-run", "", [], []

    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception:
        return explicit_task_id or target_file.stem, "", [], []

    task_id = target_file.stem
    task_title = ""
    acceptance_criteria: list[str] = []
    unresolved_criteria: list[str] = []

    for line in content.splitlines():
        line_strip = line.strip()
        if not task_title and line_strip.startswith("# "):
            task_title = line_strip[2:].strip()
        if line_strip.startswith("- [x] ") or line_strip.startswith("- [X] "):
            crit = line_strip[6:].strip()
            if crit:
                acceptance_criteria.append(crit)
        elif line_strip.startswith("- [ ] "):
            crit = line_strip[6:].strip()
            if crit:
                acceptance_criteria.append(crit)
                unresolved_criteria.append(crit)

    return task_id, task_title, acceptance_criteria, unresolved_criteria


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
