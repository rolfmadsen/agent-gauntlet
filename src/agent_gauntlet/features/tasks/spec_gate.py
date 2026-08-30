"""Shift-Left Specification and Business Rules Gatekeeper Engine.

Verifies task packages for explicit business rules (Must NOT), executable
acceptance criteria, and validates domain glossary compliance in CONTEXT.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent_gauntlet.features.diagnostics.models import DiagnosticFinding, FindingType
from agent_gauntlet.features.okf.validator import parse_frontmatter
from agent_gauntlet.features.tasks.models import TaskPackageInfo
from agent_gauntlet.features.tasks.parser import parse_task_file


@dataclass(frozen=True)
class SpecReadinessReport:
    """Consolidated assessment of task specification readiness and business rules integrity."""

    is_valid: bool
    task_id: str
    diagnostics: list[DiagnosticFinding] = field(default_factory=list)
    inspected_files: list[str] = field(default_factory=list)
    must_not_rules: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serializes the report to a dictionary for CLI or JSON consumption."""
        return {
            "is_valid": self.is_valid,
            "task_id": self.task_id,
            "inspected_files": self.inspected_files,
            "must_not_count": len(self.must_not_rules),
            "acceptance_criteria_count": len(self.acceptance_criteria),
            "must_not_rules": self.must_not_rules,
            "acceptance_criteria": self.acceptance_criteria,
            "diagnostics": [
                {
                    "file_path": d.file_path,
                    "rule": d.tool_name,
                    "message": d.message,
                    "remediation_hint": d.remediation_hint,
                }
                for d in self.diagnostics
            ],
        }


def check_task_specification(task_path: Path, workspace: Path) -> SpecReadinessReport:
    """Evaluates a task package file for specification completeness and business rules.

    Args:
        task_path: Path to the target task markdown file.
        workspace: Path to repository workspace root.

    Returns:
        SpecReadinessReport containing validation status and actionable diagnostics.
    """
    resolved_task = task_path if task_path.is_absolute() else (workspace / task_path).resolve()
    diagnostics: list[DiagnosticFinding] = []
    inspected_files: list[str] = []

    try:
        rel_task = str(resolved_task.relative_to(workspace.resolve()))
    except ValueError:
        rel_task = str(resolved_task)

    if not resolved_task.is_file():
        diagnostics.append(
            DiagnosticFinding(
                finding_type=FindingType.GENERAL_ERROR,
                tool_name="TASK_FILE_NOT_FOUND",
                file_path=rel_task,
                message=f"Task file '{resolved_task}' does not exist.",
                remediation_hint="Specify a valid path to an existing task file in tasks/.",
            )
        )
        return SpecReadinessReport(
            is_valid=False,
            task_id=resolved_task.stem,
            diagnostics=diagnostics,
            inspected_files=inspected_files,
        )

    inspected_files.append(rel_task)
    raw_content = resolved_task.read_text(encoding="utf-8")

    # 1. OKF Frontmatter Validation
    metadata, _, _ = parse_frontmatter(raw_content)
    if not metadata:
        diagnostics.append(
            DiagnosticFinding(
                finding_type=FindingType.GENERAL_ERROR,
                tool_name="INVALID_OKF_METADATA",
                file_path=rel_task,
                message="Task file is missing required Open Knowledge Format (OKF v0.2) YAML frontmatter.",
                remediation_hint="Add YAML frontmatter with 'type: Task Package', 'title', 'status', and 'generated' block.",
            )
        )

    # 2. Parse Task Package Information
    task_info: TaskPackageInfo = parse_task_file(resolved_task)

    # 3. Validate Purpose (Formål)
    has_purpose = "formål" in raw_content.lower() or "## purpose" in raw_content.lower()
    if not has_purpose:
        diagnostics.append(
            DiagnosticFinding(
                finding_type=FindingType.GENERAL_ERROR,
                tool_name="MISSING_PURPOSE",
                file_path=rel_task,
                message="Task specification is missing a '## 🎯 Formål' or '## Purpose' section.",
                remediation_hint="Add a '## 🎯 Formål' section detailing the concrete objective and scope.",
            )
        )

    # 4. Validate Acceptance Criteria (Acceptkriterier)
    if not task_info.acceptance_criteria:
        diagnostics.append(
            DiagnosticFinding(
                finding_type=FindingType.GENERAL_ERROR,
                tool_name="MISSING_ACCEPTANCE_CRITERIA",
                file_path=rel_task,
                message="Task specification is missing executable acceptance criteria items ('- [ ]').",
                remediation_hint="Add concrete '- [ ]' acceptance criteria under '## 📋 Acceptance Criteria'.",
            )
        )

    # 5. Validate Business Rules (Must NOT Invariants)
    if not task_info.must_not:
        diagnostics.append(
            DiagnosticFinding(
                finding_type=FindingType.GENERAL_ERROR,
                tool_name="MISSING_MUST_NOT",
                file_path=rel_task,
                message="Task specification is missing negative business constraints and invariants under '## 🚫 Must NOT'.",
                remediation_hint=(
                    "Add at least one explicit negative constraint or boundary under '## 🚫 Must NOT' "
                    "to prevent unauthorized architectural deviations."
                ),
            )
        )

    # 6. Check CONTEXT.md Glossary Format
    context_diagnostics = validate_context_glossary(workspace)
    diagnostics.extend(context_diagnostics)
    if (workspace / "CONTEXT.md").is_file():
        inspected_files.append("CONTEXT.md")

    is_valid = len(diagnostics) == 0
    return SpecReadinessReport(
        is_valid=is_valid,
        task_id=task_info.task_id or resolved_task.stem,
        diagnostics=diagnostics,
        inspected_files=inspected_files,
        must_not_rules=task_info.must_not,
        acceptance_criteria=task_info.acceptance_criteria,
    )


def validate_context_glossary(workspace: Path) -> list[DiagnosticFinding]:
    """Validates that CONTEXT.md follows the Aristotle definition format.

    Format rule:
    **Term**:
    <Definition sentence with genus + differentia>
    _Avoid_: <forbidden synonyms>

    Args:
        workspace: Path to workspace root.

    Returns:
        List of DiagnosticFinding items for any format violations.
    """
    context_path = workspace / "CONTEXT.md"
    if not context_path.is_file():
        return [
            DiagnosticFinding(
                finding_type=FindingType.GENERAL_ERROR,
                tool_name="MISSING_CONTEXT_GLOSSARY",
                file_path="CONTEXT.md",
                message="Missing 'CONTEXT.md' ubiquitous language glossary in workspace root.",
                remediation_hint="Create CONTEXT.md defining core domain terms using Aristotle's formula.",
            )
        ]

    content = context_path.read_text(encoding="utf-8")
    diagnostics: list[DiagnosticFinding] = []

    # Find all bold term definitions: **Term**:
    term_pattern = r"\*\*([A-Za-z0-9_ -]+)\*\*:\s*\n(.*?)(?=\n\*\*[A-Za-z0-9_ -]+\*\*:|\Z)"
    matches = list(re.finditer(term_pattern, content, re.DOTALL))

    if not matches:
        diagnostics.append(
            DiagnosticFinding(
                finding_type=FindingType.GENERAL_ERROR,
                tool_name="ARISTOTLE_FORMAT_VIOLATION",
                file_path="CONTEXT.md",
                message="No valid Aristotle glossary terms ('**Term**:') found in CONTEXT.md.",
                remediation_hint="Define terms using '**Term**:\\n<Definition>\\n_Avoid_: <synonyms>'.",
            )
        )
        return diagnostics

    for match in matches:
        term_name = match.group(1).strip()
        body = match.group(2).strip()

        # Check for _Avoid_: line
        has_avoid = "_avoid_:" in body.lower() or "_avoid:" in body.lower()
        if not has_avoid:
            diagnostics.append(
                DiagnosticFinding(
                    finding_type=FindingType.GENERAL_ERROR,
                    tool_name="ARISTOTLE_FORMAT_VIOLATION",
                    file_path="CONTEXT.md",
                    message=f"Term '{term_name}' in CONTEXT.md is missing an '_Avoid_:' line with prohibited synonyms.",
                    remediation_hint=f"Add '_Avoid_: <synonyms>' under '**{term_name}**:' definition.",
                )
            )

    return diagnostics
