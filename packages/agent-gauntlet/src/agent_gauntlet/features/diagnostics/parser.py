"""Unified diagnostic parser orchestrator for extracting structured findings from layer outputs."""

from __future__ import annotations

from typing import Sequence

from agent_gauntlet.features.diagnostics.extractors.invariants import (
    extract_fastcheck_findings,
    extract_hypothesis_findings,
    extract_proptest_findings,
)
from agent_gauntlet.features.diagnostics.extractors.linters import (
    extract_clippy_findings,
    extract_eslint_findings,
    extract_ruff_findings,
)
from agent_gauntlet.features.diagnostics.extractors.mutants import (
    extract_cargo_mutants_findings,
    extract_mutants_py_findings,
    extract_stryker_findings,
)
from agent_gauntlet.features.diagnostics.extractors.tests import (
    extract_cargo_test_findings,
    extract_pytest_findings,
    extract_unittest_findings,
    extract_vitest_findings,
)
from agent_gauntlet.features.diagnostics.extractors.types import (
    extract_cargo_check_findings,
    extract_mypy_findings,
    extract_pyright_findings,
    extract_tsc_findings,
)
from agent_gauntlet.features.diagnostics.models import (
    DiagnosticFinding,
    DiagnosticReport,
    FindingType,
)


class DiagnosticParser:
    """Orchestrates extraction of actionable findings across diverse tools and layers."""

    def parse_layer_output(
        self,
        layer_name: str,
        command: Sequence[str],
        exit_code: int,
        output: str,
    ) -> DiagnosticReport:
        """Parse raw output of a verification layer into a structured DiagnosticReport."""
        passed = exit_code == 0
        cmd_str = " ".join(command).lower()
        findings: list[DiagnosticFinding] = []

        if not passed:
            # 1. Linters
            if "ruff" in cmd_str:
                findings.extend(extract_ruff_findings(output))
            elif "eslint" in cmd_str or "biome" in cmd_str:
                findings.extend(extract_eslint_findings(output))
            elif "clippy" in cmd_str:
                findings.extend(extract_clippy_findings(output))

            # 2. Type Checkers
            if "pyright" in cmd_str:
                findings.extend(extract_pyright_findings(output))
            elif "mypy" in cmd_str:
                findings.extend(extract_mypy_findings(output))
            elif "tsc" in cmd_str:
                findings.extend(extract_tsc_findings(output))
            elif "cargo check" in cmd_str:
                findings.extend(extract_cargo_check_findings(output))

            # 3. Test Runners & Invariants
            if "pytest" in cmd_str:
                findings.extend(extract_pytest_findings(output))
                findings.extend(extract_hypothesis_findings(output))
            elif "unittest" in cmd_str:
                findings.extend(extract_unittest_findings(output))
            elif "vitest" in cmd_str or "jest" in cmd_str or "npm test" in cmd_str:
                findings.extend(extract_vitest_findings(output))
                findings.extend(extract_fastcheck_findings(output))
            elif "cargo test" in cmd_str:
                findings.extend(extract_cargo_test_findings(output))
                findings.extend(extract_proptest_findings(output))

            # 4. Mutation Testing
            if "mutants.py" in cmd_str:
                findings.extend(extract_mutants_py_findings(output))
            elif "stryker" in cmd_str:
                findings.extend(extract_stryker_findings(output))
            elif "cargo-mutants" in cmd_str or "cargo mutants" in cmd_str:
                findings.extend(extract_cargo_mutants_findings(output))

            # 5. General Fallback if no specific extractor found findings
            if not findings and exit_code != 0:
                first_lines = "\n".join(output.strip().splitlines()[:5])
                findings.append(
                    DiagnosticFinding(
                        finding_type=FindingType.GENERAL_ERROR,
                        tool_name=layer_name,
                        file_path="",
                        line_number=None,
                        column_number=None,
                        message=f"Layer '{layer_name}' failed with exit code {exit_code}.",
                        remediation_hint=f"Check layer logs and fix underlying command execution failure in '{' '.join(command)}'.",
                        raw_context=first_lines,
                    )
                )

        summary = f"Layer '{layer_name}': {'PASSED' if passed else 'FAILED'} with {len(findings)} findings (exit code {exit_code})"

        return DiagnosticReport(
            layer_name=layer_name,
            passed=passed,
            exit_code=exit_code,
            findings=findings,
            summary=summary,
        )
