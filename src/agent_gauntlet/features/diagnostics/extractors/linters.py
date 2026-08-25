"""Parsers and extractors for linter outputs (Ruff, ESLint, Clippy, Flake8)."""

from __future__ import annotations

import re

from agent_gauntlet.features.diagnostics.models import DiagnosticFinding, FindingType


def extract_ruff_findings(output: str) -> list[DiagnosticFinding]:
    """
    Extract findings from Ruff output.
    Pattern: filepath:line:col: RULE_CODE message
    """
    findings: list[DiagnosticFinding] = []
    pattern = re.compile(r"^([^:\n]+):(\d+):(\d+):\s+([A-Z0-9]+)\s+(.+)$", re.MULTILINE)

    for match in pattern.finditer(output):
        file_path, line_str, col_str, code, msg = match.groups()
        hint = f"Resolve Ruff rule {code}. Run 'ruff check --fix' or adjust code formatting/imports."
        if code.startswith("F401"):
            hint = "Unused import: Remove the unused import statement or use the symbol."
        elif code.startswith("E501"):
            hint = "Line length exceeded: Refactor or wrap the statement onto multiple lines."
        elif code.startswith("F841"):
            hint = "Unused local variable: Remove or rename to '_' if intentionally unused."

        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.LINT_ERROR,
                tool_name="ruff",
                file_path=file_path.strip(),
                line_number=int(line_str),
                column_number=int(col_str),
                message=f"{code} {msg.strip()}",
                remediation_hint=hint,
                raw_context=match.group(0),
            )
        )
    return findings


def extract_eslint_findings(output: str) -> list[DiagnosticFinding]:
    """
    Extract findings from ESLint / Biome output.
    Pattern: filepath:line:col: error/warning: message (rule)
    """
    findings: list[DiagnosticFinding] = []
    # Pattern 1: /path/file.ts:10:5: error: message (rule)
    pattern1 = re.compile(
        r"^([^:\n]+):(\d+):(\d+):\s+(?:error|warning):\s+(.+?)(?:\s+\(([^)]+)\))?$",
        re.MULTILINE | re.IGNORECASE,
    )
    # Pattern 2: line:col error message rule
    pattern2 = re.compile(
        r"^\s*(\d+):(\d+)\s+(?:error|warning)\s+(.+?)\s+([@\w\-/]+)$",
        re.MULTILINE | re.IGNORECASE,
    )

    for match in pattern1.finditer(output):
        file_path, line_str, col_str, msg, rule = match.groups()
        rule_name = rule or "eslint-rule"
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.LINT_ERROR,
                tool_name="eslint",
                file_path=file_path.strip(),
                line_number=int(line_str),
                column_number=int(col_str),
                message=msg.strip(),
                remediation_hint=f"Fix ESLint rule '{rule_name}' in {file_path}:{line_str}.",
                raw_context=match.group(0),
            )
        )

    if not findings:
        current_file = ""
        for line in output.splitlines():
            if line.startswith("/") or line.startswith("./") or line.endswith(".ts") or line.endswith(".tsx") or line.endswith(".js"):
                if not line.startswith(" "):
                    current_file = line.strip()
            m = pattern2.match(line)
            if m and current_file:
                line_str, col_str, msg, rule = m.groups()
                findings.append(
                    DiagnosticFinding(
                        finding_type=FindingType.LINT_ERROR,
                        tool_name="eslint",
                        file_path=current_file,
                        line_number=int(line_str),
                        column_number=int(col_str),
                        message=f"{msg} ({rule})",
                        remediation_hint=f"Fix ESLint rule '{rule}'.",
                        raw_context=line.strip(),
                    )
                )

    return findings


def extract_clippy_findings(output: str) -> list[DiagnosticFinding]:
    """
    Extract findings from Cargo Clippy output.
    Pattern:
    error/warning: message
      --> path/to/file.rs:line:col
    """
    findings: list[DiagnosticFinding] = []
    pattern = re.compile(
        r"(?:error|warning):\s+(.+?)\n\s+-->\s+([^:\n]+):(\d+):(\d+)",
        re.MULTILINE,
    )

    for match in pattern.finditer(output):
        msg, file_path, line_str, col_str = match.groups()
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.LINT_ERROR,
                tool_name="clippy",
                file_path=file_path.strip(),
                line_number=int(line_str),
                column_number=int(col_str),
                message=msg.strip(),
                remediation_hint=f"Apply Clippy fix in {file_path}:{line_str}:{col_str}.",
                raw_context=match.group(0),
            )
        )
    return findings
