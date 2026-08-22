"""Parsers and extractors for test runners (Pytest, Unittest, Vitest, Jest, Cargo Test)."""

from __future__ import annotations

import re
from agent_gauntlet.features.diagnostics.models import DiagnosticFinding, FindingType


def extract_pytest_findings(output: str) -> list[DiagnosticFinding]:
    """Extract failed tests from pytest summary and failure blocks."""
    findings: list[DiagnosticFinding] = []

    # Pattern: FAILED path/to/test_file.py::test_name - AssertionError: ...
    summary_pattern = re.compile(
        r"^FAILED\s+([^:\n]+?)::([^\s\-]+)\s*-\s*(.+)$",
        re.MULTILINE,
    )
    for match in summary_pattern.finditer(output):
        file_path, test_name, reason = match.groups()
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.TEST_FAILURE,
                tool_name="pytest",
                file_path=file_path.strip(),
                line_number=None,
                message=f"Test failure in {test_name}: {reason.strip()}",
                remediation_hint=f"Examine failing test '{test_name}' and fix root cause assertion.",
                raw_context=match.group(0),
            )
        )

    # Fallback to failure traceback block if summary pattern didn't match
    if not findings:
        block_pattern = re.compile(
            r"_{3,}\s+([^\s]+)\s+_{3,}\n([^:\n]+):(\d+): in \1\n(?:.*?\n)*?E\s+(.+)",
            re.MULTILINE,
        )
        for match in block_pattern.finditer(output):
            test_name, file_path, line_str, err_msg = match.groups()
            findings.append(
                DiagnosticFinding(
                    finding_type=FindingType.TEST_FAILURE,
                    tool_name="pytest",
                    file_path=file_path.strip(),
                    line_number=int(line_str),
                    message=f"{test_name}: {err_msg.strip()}",
                    remediation_hint=f"Fix assertion error in {file_path}:{line_str}.",
                    raw_context=match.group(0),
                )
            )

    return findings


def extract_unittest_findings(output: str) -> list[DiagnosticFinding]:
    """Extract failed tests from standard python unittest runner output."""
    findings: list[DiagnosticFinding] = []

    # Pattern: FAIL/ERROR: test_name (module.Class.test_name)
    test_head_pattern = re.compile(
        r"^(?:FAIL|ERROR):\s+([^\s]+)\s+\(([^)]+)\)\n-+?\nTraceback \(most recent call last\):\n(?:.*?\n)*?\s+File \"([^\"]+)\", line (\d+), in [^\n]+\n(?:.*?\n)*?([A-Za-z0-9_]+Error:[^\n]+)",
        re.MULTILINE,
    )

    for match in test_head_pattern.finditer(output):
        test_name, test_class, file_path, line_str, err_msg = match.groups()
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.TEST_FAILURE,
                tool_name="unittest",
                file_path=file_path.strip(),
                line_number=int(line_str),
                message=f"{test_class}.{test_name} - {err_msg.strip()}",
                remediation_hint=f"Review test failure in {file_path}:{line_str}.",
                raw_context=match.group(0),
            )
        )

    # Simplified fallback if traceback parsing missed
    if not findings:
        simple_pattern = re.compile(
            r"^(?:FAIL|ERROR):\s+([^\s]+)\s+\(([^)]+)\)",
            re.MULTILINE,
        )
        for match in simple_pattern.finditer(output):
            test_name, test_class = match.groups()
            findings.append(
                DiagnosticFinding(
                    finding_type=FindingType.TEST_FAILURE,
                    tool_name="unittest",
                    file_path="",
                    line_number=None,
                    message=f"Test failure in {test_class}.{test_name}",
                    remediation_hint="Inspect unittest output and implement failing test expectations.",
                    raw_context=match.group(0),
                )
            )

    return findings


def extract_vitest_findings(output: str) -> list[DiagnosticFinding]:
    """Extract failed tests from Vitest / Jest output."""
    findings: list[DiagnosticFinding] = []

    # Pattern: FAIL path/to/file.ts > Suite > test
    pattern = re.compile(
        r"FAIL\s+([^\n>]+?)(?:\s+>\s+([^\n]+))?\n(?:.*?\n)*?\s*(?:AssertionError|Error):\s+([^\n]+)\n\s+❯\s+([^:\n]+):(\d+)",
        re.MULTILINE,
    )

    for match in pattern.finditer(output):
        suite_path, test_desc, err_msg, file_path, line_str = match.groups()
        desc = test_desc or "test"
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.TEST_FAILURE,
                tool_name="vitest",
                file_path=file_path.strip(),
                line_number=int(line_str),
                message=f"{desc}: {err_msg.strip()}",
                remediation_hint=f"Fix Vitest failure in {file_path}:{line_str}.",
                raw_context=match.group(0),
            )
        )
    return findings


def extract_cargo_test_findings(output: str) -> list[DiagnosticFinding]:
    """Extract failed tests from cargo test output."""
    findings: list[DiagnosticFinding] = []

    pattern = re.compile(
        r"----\s+([^\s]+)\s+stdout\s+----\n(?:.*?\n)*?thread '[^']+' panicked at ([^:\n]+):(\d+):(\d+):\n([^\n]+)",
        re.MULTILINE,
    )

    for match in pattern.finditer(output):
        test_name, file_path, line_str, col_str, panic_msg = match.groups()
        findings.append(
            DiagnosticFinding(
                finding_type=FindingType.TEST_FAILURE,
                tool_name="cargo-test",
                file_path=file_path.strip(),
                line_number=int(line_str),
                column_number=int(col_str),
                message=f"{test_name} panicked: {panic_msg.strip()}",
                remediation_hint=f"Fix test assertion/panic in {file_path}:{line_str}.",
                raw_context=match.group(0),
            )
        )
    return findings
