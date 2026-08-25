"""Parsers and extractors for static type checker outputs (Pyright, Mypy, tsc, cargo check)."""

from __future__ import annotations

import re

from agent_gauntlet.features.diagnostics.models import DiagnosticFinding, FindingType


def extract_pyright_findings(output: str) -> list[DiagnosticFinding]:
    """
    Extract findings from Pyright output.
    Pattern: filepath:line:col - error/warning: message (rule)
    """
    findings: list[DiagnosticFinding] = []
    pattern = re.compile(
        r"^([^:\n]+):(\d+):(\d+)\s+-\s+(?:error|warning|information):\s+(.+?)(?:\s+\(([^)]+)\))?$",
        re.MULTILINE,
    )

    for match in pattern.finditer(output):
        file_path, line_str, col_str, msg, rule = match.groups()
        rule_name = rule or "type-check"
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.TYPE_MISMATCH,
                tool_name="pyright",
                file_path=file_path.strip(),
                line_number=int(line_str),
                column_number=int(col_str),
                message=msg.strip(),
                remediation_hint=f"Type error ({rule_name}): Ensure type signature aligns with parameter/return constraints.",
                raw_context=match.group(0),
            )
        )
    return findings


def extract_mypy_findings(output: str) -> list[DiagnosticFinding]:
    """
    Extract findings from Mypy output.
    Pattern: filepath:line: error/note: message [rule]
    """
    findings: list[DiagnosticFinding] = []
    pattern = re.compile(
        r"^([^:\n]+):(\d+):\s+(?:error|note):\s+(.+?)(?:\s+\[([^\]]+)\])?$",
        re.MULTILINE,
    )

    for match in pattern.finditer(output):
        file_path, line_str, msg, rule = match.groups()
        rule_name = rule or "type-error"
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.TYPE_MISMATCH,
                tool_name="mypy",
                file_path=file_path.strip(),
                line_number=int(line_str),
                column_number=None,
                message=msg.strip(),
                remediation_hint=f"Mypy error [{rule_name}]: Fix type annotation or type conversion.",
                raw_context=match.group(0),
            )
        )
    return findings


def extract_tsc_findings(output: str) -> list[DiagnosticFinding]:
    """
    Extract findings from TypeScript compiler (tsc) output.
    Pattern: filepath(line,col): error TSXXXX: message
    """
    findings: list[DiagnosticFinding] = []
    pattern = re.compile(
        r"^([^(:\n]+)\((\d+),(\d+)\):\s+(?:error|warning)\s+(TS\d+):\s+(.+)$",
        re.MULTILINE,
    )

    for match in pattern.finditer(output):
        file_path, line_str, col_str, ts_code, msg = match.groups()
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.TYPE_MISMATCH,
                tool_name="tsc",
                file_path=file_path.strip(),
                line_number=int(line_str),
                column_number=int(col_str),
                message=f"{ts_code}: {msg.strip()}",
                remediation_hint=f"Resolve TypeScript compiler error {ts_code}.",
                raw_context=match.group(0),
            )
        )
    return findings


def extract_cargo_check_findings(output: str) -> list[DiagnosticFinding]:
    """
    Extract findings from cargo check output.
    """
    findings: list[DiagnosticFinding] = []
    pattern = re.compile(
        r"error(?:\[E\d+\])?:\s+(.+?)\n\s+-->\s+([^:\n]+):(\d+):(\d+)",
        re.MULTILINE,
    )

    for match in pattern.finditer(output):
        msg, file_path, line_str, col_str = match.groups()
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.TYPE_MISMATCH,
                tool_name="cargo-check",
                file_path=file_path.strip(),
                line_number=int(line_str),
                column_number=int(col_str),
                message=msg.strip(),
                remediation_hint=f"Fix compiler type/borrow error in {file_path}:{line_str}.",
                raw_context=match.group(0),
            )
        )
    return findings
