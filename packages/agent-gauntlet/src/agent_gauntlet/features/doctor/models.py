"""Data models for agent-gauntlet doctor diagnostics and integrity engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FindingSeverity(str, Enum):
    """Severity levels for doctor diagnostic findings."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class DoctorFinding:
    """Individual finding reported by the workspace integrity scanner."""

    severity: FindingSeverity
    category: str
    path: str
    message: str
    remediation: str

    def to_dict(self) -> dict[str, Any]:
        """Converts finding to serializable dictionary."""
        return {
            "severity": self.severity.value,
            "category": self.category,
            "path": self.path,
            "message": self.message,
            "remediation": self.remediation,
        }


@dataclass
class DoctorReport:
    """Consolidated workspace diagnostic report and AI migration guide."""

    workspace: str
    healthy: bool
    has_errors: bool
    findings: list[DoctorFinding] = field(default_factory=list)
    migration_prompt: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Converts doctor report to serializable dictionary."""
        return {
            "workspace": self.workspace,
            "healthy": self.healthy,
            "has_errors": self.has_errors,
            "findings": [f.to_dict() for f in self.findings],
            "migration_prompt": self.migration_prompt,
        }

    def format_terminal(self) -> str:
        """Formats the doctor report for terminal presentation."""
        lines = []
        status_label = (
            "HEALTHY" if self.healthy else ("DEGRADED" if not self.has_errors else "UNHEALTHY")
        )
        lines.append(f"[{status_label}] agent-gauntlet doctor report for '{self.workspace}':")

        if self.healthy and not self.findings:
            lines.append(
                "  [+] All required configuration, specifications, tasks, and skill references are intact."
            )
            return "\n".join(lines)

        lines.append("")
        for f in self.findings:
            tag = (
                "[!]"
                if f.severity == FindingSeverity.ERROR
                else ("[*]" if f.severity == FindingSeverity.WARNING else "[i]")
            )
            lines.append(f"  {tag} {f.severity.value} [{f.category}] {f.path}:")
            lines.append(f"      {f.message}")
            if f.remediation:
                lines.append(f"      Fix: {f.remediation}")

        if self.migration_prompt:
            lines.append("")
            lines.append("=" * 60)
            lines.append("📋 Tailored AI Migration Prompt (Copy & Paste to your Agent):")
            lines.append("=" * 60)
            lines.append(self.migration_prompt)
            lines.append("=" * 60)

        return "\n".join(lines)
