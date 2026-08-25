"""Unit tests for diagnostic models, extractors, and unified parser."""

import unittest

from agent_gauntlet.features.diagnostics.extractors.invariants import (
    extract_hypothesis_findings,
)
from agent_gauntlet.features.diagnostics.extractors.linters import (
    extract_clippy_findings,
    extract_eslint_findings,
    extract_ruff_findings,
)
from agent_gauntlet.features.diagnostics.extractors.mutants import (
    extract_mutants_py_findings,
)
from agent_gauntlet.features.diagnostics.extractors.tests import (
    extract_pytest_findings,
    extract_unittest_findings,
    extract_vitest_findings,
)
from agent_gauntlet.features.diagnostics.extractors.types import (
    extract_mypy_findings,
    extract_pyright_findings,
    extract_tsc_findings,
)
from agent_gauntlet.features.diagnostics.models import (
    FindingType,
)
from agent_gauntlet.features.diagnostics.parser import DiagnosticParser


class TestLinterExtractors(unittest.TestCase):
    """Tests for lint tool output parsers."""

    def test_extract_ruff_findings(self) -> None:
        raw_output = """
src/auth/service.py:42:10: F401 `os` imported but unused
src/auth/service.py:88:1: E501 Line too long (95 > 88)
Found 2 errors.
"""
        findings = extract_ruff_findings(raw_output)
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0].finding_type, FindingType.LINT_ERROR)
        self.assertEqual(findings[0].file_path, "src/auth/service.py")
        self.assertEqual(findings[0].line_number, 42)
        self.assertEqual(findings[0].column_number, 10)
        self.assertIn("F401", findings[0].message)
        self.assertIn("Unused import", findings[0].remediation_hint)

    def test_extract_eslint_findings(self) -> None:
        raw_output = """
/app/src/index.ts:15:3: error: Unexpected 'any'. Specify a different type (@typescript-eslint/no-explicit-any)
1 problem (1 error, 0 warnings)
"""
        findings = extract_eslint_findings(raw_output)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].finding_type, FindingType.LINT_ERROR)
        self.assertEqual(findings[0].file_path, "/app/src/index.ts")
        self.assertEqual(findings[0].line_number, 15)
        self.assertEqual(findings[0].column_number, 3)

    def test_extract_clippy_findings(self) -> None:
        raw_output = """
error: this let-binding has unit value
  --> src/main.rs:12:5
   |
12 |     let () = do_something();
   |     ^^^^^^^^^^^^^^^^^^^^^^^^ help: omit the `let () =`
"""
        findings = extract_clippy_findings(raw_output)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].finding_type, FindingType.LINT_ERROR)
        self.assertEqual(findings[0].file_path, "src/main.rs")
        self.assertEqual(findings[0].line_number, 12)
        self.assertEqual(findings[0].column_number, 5)


class TestTypeExtractors(unittest.TestCase):
    """Tests for static type checker output parsers."""

    def test_extract_pyright_findings(self) -> None:
        raw_output = """
/repo/src/core.py:25:9 - error: Argument of type "int" cannot be assigned to parameter "name" of type "str" (reportArgumentType)
1 error, 0 warnings, 0 informations
"""
        findings = extract_pyright_findings(raw_output)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].finding_type, FindingType.TYPE_MISMATCH)
        self.assertEqual(findings[0].file_path, "/repo/src/core.py")
        self.assertEqual(findings[0].line_number, 25)
        self.assertEqual(findings[0].column_number, 9)

    def test_extract_mypy_findings(self) -> None:
        raw_output = """
src/utils.py:10: error: Incompatible return value type (got "int", expected "str") [return-value]
Found 1 error in 1 file (checked 1 source file)
"""
        findings = extract_mypy_findings(raw_output)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].finding_type, FindingType.TYPE_MISMATCH)
        self.assertEqual(findings[0].file_path, "src/utils.py")
        self.assertEqual(findings[0].line_number, 10)

    def test_extract_tsc_findings(self) -> None:
        raw_output = """
src/models/user.ts(24,5): error TS2322: Type 'string' is not assignable to type 'number'.
"""
        findings = extract_tsc_findings(raw_output)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].finding_type, FindingType.TYPE_MISMATCH)
        self.assertEqual(findings[0].file_path, "src/models/user.ts")
        self.assertEqual(findings[0].line_number, 24)
        self.assertEqual(findings[0].column_number, 5)


class TestTestExtractors(unittest.TestCase):
    """Tests for unit and test framework output parsers."""

    def test_extract_pytest_findings(self) -> None:
        raw_output = """
=================================== FAILURES ===================================
_________________________________ test_login __________________________________
tests/test_auth.py:45: in test_login
    assert user.is_authenticated is True
E   AssertionError: assert False is True
=========================== short test summary info ============================
FAILED tests/test_auth.py::test_login - AssertionError: assert False is True
1 failed, 10 passed in 0.50s
"""
        findings = extract_pytest_findings(raw_output)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].finding_type, FindingType.TEST_FAILURE)
        self.assertEqual(findings[0].file_path, "tests/test_auth.py")
        self.assertIn("AssertionError", findings[0].message)

    def test_extract_unittest_findings(self) -> None:
        raw_output = """
======================================================================
FAIL: test_validate_token (tests.test_auth.TestAuth.test_validate_token)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/repo/tests/test_auth.py", line 55, in test_validate_token
    self.assertTrue(res)
AssertionError: False is not true

----------------------------------------------------------------------
Ran 5 tests in 0.010s

FAILED (failures=1)
"""
        findings = extract_unittest_findings(raw_output)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].finding_type, FindingType.TEST_FAILURE)
        self.assertEqual(findings[0].file_path, "/home/repo/tests/test_auth.py")
        self.assertEqual(findings[0].line_number, 55)

    def test_extract_vitest_findings(self) -> None:
        raw_output = """
FAIL  tests/calculator.test.ts > Calculator > adds two numbers
AssertionError: expected 4 to deeply equal 5
 ❯ tests/calculator.test.ts:18:24
"""
        findings = extract_vitest_findings(raw_output)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].finding_type, FindingType.TEST_FAILURE)
        self.assertEqual(findings[0].file_path, "tests/calculator.test.ts")
        self.assertEqual(findings[0].line_number, 18)


class TestInvariantAndMutantExtractors(unittest.TestCase):
    """Tests for property-based and mutation testing extractors."""

    def test_extract_hypothesis_findings(self) -> None:
        raw_output = """
Falsifying example: test_encode_decode(
    s='',
)
Traceback (most recent call last):
  File "tests/test_props.py", line 30, in test_encode_decode
    assert decode(encode(s)) == s
AssertionError
"""
        findings = extract_hypothesis_findings(raw_output)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].finding_type, FindingType.PROPERTY_VIOLATION)
        self.assertEqual(findings[0].file_path, "tests/test_props.py")
        self.assertEqual(findings[0].line_number, 30)

    def test_extract_mutants_py_findings(self) -> None:
        raw_output = """
=== Mutation Testing Gauntlet ===
M1 drop empty layers validation: KILLED
M2 invert passed returncode comparison: SURVIVED
M3 invert failure detection check: KILLED

1/3 mutants survived
"""
        findings = extract_mutants_py_findings(raw_output)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].finding_type, FindingType.MUTANT_SURVIVED)
        self.assertIn("M2 invert passed returncode comparison", findings[0].message)
        self.assertIn("Strengthen test assertions", findings[0].remediation_hint)


class TestUnifiedDiagnosticParser(unittest.TestCase):
    """Tests for top-level DiagnosticParser dispatching."""

    def test_parser_dispatches_correctly_and_summarizes(self) -> None:
        parser = DiagnosticParser()
        report = parser.parse_layer_output(
            layer_name="lint",
            command=["ruff", "check", "."],
            exit_code=1,
            output="src/app.py:10:1: F401 `sys` imported but unused",
        )
        self.assertFalse(report.passed)
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings[0].finding_type, FindingType.LINT_ERROR)
        self.assertIn("app.py", report.findings[0].file_path)


if __name__ == "__main__":
    unittest.main()
