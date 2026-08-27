"""Parser and resolver for task markdown files and task contracts."""

from __future__ import annotations

import re
from pathlib import Path

from agent_gauntlet.features.tasks.models import (
    ALLOWED_ACTIVE_STATUSES,
    TaskPackageInfo,
    TaskStatus,
)


def parse_task_status(content: str) -> TaskStatus:
    """Extract and normalize task status from task markdown content."""
    status_match = re.search(r"\*\*Status\*\*:\s*`?([A-Za-z0-9_-]+)`?", content, re.IGNORECASE)
    if status_match:
        return TaskStatus.from_string(status_match.group(1))

    # Also check YAML frontmatter or simple header line
    header_match = re.search(r"(?:^|\n)status:\s*`?([A-Za-z0-9_-]+)`?", content, re.IGNORECASE)
    if header_match:
        return TaskStatus.from_string(header_match.group(1))

    header_status = re.search(r"\bStatus:\s*`?([A-Za-z0-9_-]+)`?", content, re.IGNORECASE)
    if header_status:
        return TaskStatus.from_string(header_status.group(1))

    return TaskStatus.UNKNOWN


def is_task_active(content: str) -> bool:
    """
    Check if task file content represents an actively approved task.
    Strictly requires an explicit allowed status (ACTIVE, IN_PROGRESS, WIP, TODO, REOPENED)
    AND non-empty acceptance criteria. DRAFT, REJECTED, or missing status are NEVER active.
    """
    status = parse_task_status(content)
    if status not in ALLOWED_ACTIVE_STATUSES:
        return False

    has_criteria = "acceptance criteria" in content.lower() or "- [" in content
    return has_criteria


def has_active_task(workspace: Path) -> bool:
    """Determine whether the workspace has at least one active task in tasks/."""
    tasks_dir = workspace / "tasks"
    if not tasks_dir.is_dir():
        return False

    for candidate in sorted(tasks_dir.glob("*.md")):
        try:
            content = candidate.read_text(encoding="utf-8")
            if is_task_active(content):
                return True
        except Exception:
            continue

    return False


def parse_task_file(path: Path) -> TaskPackageInfo:
    """Parse complete TaskPackageInfo from a markdown task file."""
    content = path.read_text(encoding="utf-8")
    status = parse_task_status(content)
    task_id = path.stem
    title = ""
    acceptance_criteria: list[str] = []
    unresolved_criteria: list[str] = []
    must_not: list[str] = []

    in_must_not = False
    for line in content.splitlines():
        line_strip = line.strip()
        if not title and line_strip.startswith("# "):
            title = line_strip[2:].strip()

        if line_strip.lower().startswith("## 🚫 must not") or line_strip.lower().startswith(
            "## must not"
        ):
            in_must_not = True
            continue
        elif line_strip.startswith("## "):
            in_must_not = False

        if in_must_not and line_strip.startswith("- "):
            item = line_strip[2:].strip()
            if item:
                must_not.append(item)

        if line_strip.startswith("- [x] ") or line_strip.startswith("- [X] "):
            crit = line_strip[6:].strip()
            if crit:
                acceptance_criteria.append(crit)
        elif line_strip.startswith("- [ ] "):
            crit = line_strip[6:].strip()
            if crit:
                acceptance_criteria.append(crit)
                unresolved_criteria.append(crit)

    return TaskPackageInfo(
        task_id=task_id,
        title=title,
        status=status,
        acceptance_criteria=acceptance_criteria,
        unresolved_criteria=unresolved_criteria,
        must_not=must_not,
    )


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
        info = parse_task_file(target_file)
        return info.task_id, info.title, info.acceptance_criteria, info.unresolved_criteria
    except Exception:
        return explicit_task_id or target_file.stem, "", [], []
