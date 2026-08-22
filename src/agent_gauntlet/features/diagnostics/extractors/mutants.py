"""Parsers and extractors for mutation testing survivors (mutants.py, Stryker, cargo-mutants)."""

from __future__ import annotations

import re
from agent_gauntlet.features.diagnostics.models import DiagnosticFinding, FindingType


def extract_mutants_py_findings(output: str) -> list[DiagnosticFinding]:
    """Extract survived synthetic mutants from tools/mutants.py output."""
    findings: list[DiagnosticFinding] = []

    pattern = re.compile(
        r"^([A-Za-z0-9_\-]+(?:\s+[^:]+)?):\s+SURVIVED$",
        re.MULTILINE,
    )

    for match in pattern.finditer(output):
        mutant_desc = match.group(1).strip()
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.MUTANT_SURVIVED,
                tool_name="mutants.py",
                file_path="",
                line_number=None,
                message=f"Mutant survived: {mutant_desc}",
                remediation_hint=f"Strengthen test assertions to kill mutant '{mutant_desc}'. Add targeted test cases for this branch/condition.",
                raw_context=match.group(0),
            )
        )
    return findings


def extract_stryker_findings(output: str) -> list[DiagnosticFinding]:
    """Extract survived mutants from Stryker mutation testing output."""
    findings: list[DiagnosticFinding] = []

    pattern = re.compile(
        r"#(\d+)\.\s+\[Survived\]\s+([^:\n]+):(\d+):(\d+)\n\s+Mutator:\s+([^\n]+)",
        re.MULTILINE,
    )

    for match in pattern.finditer(output):
        mut_id, file_path, line_str, col_str, mutator = match.groups()
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.MUTANT_SURVIVED,
                tool_name="stryker",
                file_path=file_path.strip(),
                line_number=int(line_str),
                column_number=int(col_str),
                message=f"Stryker mutant #{mut_id} ({mutator}) survived",
                remediation_hint=f"Add unit test asserting expected behavior for mutator '{mutator}' in {file_path}:{line_str}.",
                raw_context=match.group(0),
            )
        )
    return findings


def extract_cargo_mutants_findings(output: str) -> list[DiagnosticFinding]:
    """Extract survived mutants from cargo-mutants output."""
    findings: list[DiagnosticFinding] = []

    pattern = re.compile(
        r"MISSED\s+([^:\n]+):(\d+):(\d+):\s+replace\s+(.+)",
        re.MULTILINE,
    )

    for match in pattern.finditer(output):
        file_path, line_str, col_str, mutation_desc = match.groups()
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.MUTANT_SURVIVED,
                tool_name="cargo-mutants",
                file_path=file_path.strip(),
                line_number=int(line_str),
                column_number=int(col_str),
                message=f"Cargo mutant missed: replace {mutation_desc.strip()}",
                remediation_hint=f"Write test covering condition in {file_path}:{line_str}.",
                raw_context=match.group(0),
            )
        )
    return findings
