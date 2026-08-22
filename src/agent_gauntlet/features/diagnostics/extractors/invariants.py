"""Parsers and extractors for property and invariant violations (Hypothesis, Proptest, Fast-Check)."""

from __future__ import annotations

import re
from agent_gauntlet.features.diagnostics.models import DiagnosticFinding, FindingType


def extract_hypothesis_findings(output: str) -> list[DiagnosticFinding]:
    """Extract falsifying examples and stack traces from Hypothesis runs."""
    findings: list[DiagnosticFinding] = []

    pattern = re.compile(
        r"Falsifying example:\s+([^\n]+(?:\n\s+.*)*?)\n(?:.*?\n)*?\s+File \"([^\"]+)\", line (\d+), in ([^\n]+)",
        re.MULTILINE,
    )

    for match in pattern.finditer(output):
        falsifying_example, file_path, line_str, fn_name = match.groups()
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.PROPERTY_VIOLATION,
                tool_name="hypothesis",
                file_path=file_path.strip(),
                line_number=int(line_str),
                message=f"Invariant failed in {fn_name}: {falsifying_example.strip()}",
                remediation_hint="Falsifying example found by Hypothesis. Handle edge case or adjust invariant boundary.",
                raw_context=match.group(0),
            )
        )
    return findings


def extract_proptest_findings(output: str) -> list[DiagnosticFinding]:
    """Extract proptest minimal reproducing cases."""
    findings: list[DiagnosticFinding] = []

    pattern = re.compile(
        r"proptest:\s+test failed:\s+(.+?)(?:\n\s+minimal reproducing case:\s+(.+))?",
        re.MULTILINE,
    )

    for match in pattern.finditer(output):
        reason, minimal_case = match.groups()
        case_info = f" (case: {minimal_case.strip()})" if minimal_case else ""
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.PROPERTY_VIOLATION,
                tool_name="proptest",
                file_path="",
                line_number=None,
                message=f"Property failure: {reason.strip()}{case_info}",
                remediation_hint="Property failed. Fix algorithm against minimal counterexample.",
                raw_context=match.group(0),
            )
        )
    return findings


def extract_fastcheck_findings(output: str) -> list[DiagnosticFinding]:
    """Extract fast-check counterexamples."""
    findings: list[DiagnosticFinding] = []

    pattern = re.compile(
        r"Property failed after \d+ tests\s+Counterexample:\s+([^\n]+)",
        re.MULTILINE,
    )

    for match in pattern.finditer(output):
        counterexample = match.group(1)
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.PROPERTY_VIOLATION,
                tool_name="fast-check",
                file_path="",
                line_number=None,
                message=f"Property violated with counterexample: {counterexample.strip()}",
                remediation_hint="Handle counterexample in TypeScript invariant definition.",
                raw_context=match.group(0),
            )
        )
    return findings
