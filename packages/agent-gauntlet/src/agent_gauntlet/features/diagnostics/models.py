"""Diagnostic models for structured actionable feedback in agent-gauntlet."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FindingType(str, Enum):
    """Categorized diagnostic finding types."""

    LINT_ERROR = "LINT_ERROR"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    TEST_FAILURE = "TEST_FAILURE"
    PROPERTY_VIOLATION = "PROPERTY_VIOLATION"
    MUTANT_SURVIVED = "MUTANT_SURVIVED"
    DRIFT_DETECTED = "DRIFT_DETECTED"
    GENERAL_ERROR = "GENERAL_ERROR"


@dataclass
class DiagnosticFinding:
    """A single structured diagnostic finding with actionable remediation guidance."""

    finding_type: FindingType
    tool_name: str
    file_path: str = ""
    line_number: int | None = None
    column_number: int | None = None
    message: str = ""
    remediation_hint: str = ""
    raw_context: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert finding to dictionary representation."""
        return {
            "finding_type": self.finding_type.value,
            "tool_name": self.tool_name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "message": self.message,
            "remediation_hint": self.remediation_hint,
            "raw_context": self.raw_context,
        }


@dataclass
class DiagnosticReport:
    """Structured report of all diagnostic findings extracted from a verification layer."""

    layer_name: str
    passed: bool
    exit_code: int
    findings: list[DiagnosticFinding] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary representation."""
        return {
            "layer_name": self.layer_name,
            "passed": self.passed,
            "exit_code": self.exit_code,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize report to formatted JSON."""
        return json.dumps(self.to_dict(), indent=indent)
