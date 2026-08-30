"""Acceptance and unit tests for the Release Readiness and Documentation Synchronization Gate."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.cli import main
from agent_gauntlet.features.evidence.release_gate import (
    ReleaseReadinessReport,
    check_release_readiness,
)


class TestReleaseReadinessGate(unittest.TestCase):
    """Test suite verifying automated release readiness and doc sync validation."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name).resolve()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _setup_valid_workspace(self) -> None:
        (self.workspace / "pyproject.toml").write_text(
            '[project]\nname = "demo-pkg"\nversion = "0.4.0"\n', encoding="utf-8"
        )
        pkg_dir = self.workspace / "packages" / "demo-pkg"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "package.json").write_text(
            '{"name": "demo-pkg", "version": "0.4.0"}', encoding="utf-8"
        )
        (self.workspace / "CHANGELOG.md").write_text(
            "# Changelog\n\n## [0.4.0] - 2026-08-30\n- Great feature\n\n## [0.3.0] - 2026-08-20\n",
            encoding="utf-8",
        )
        adr_dir = self.workspace / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "0001-initial-architecture.md").write_text("# ADR 0001", encoding="utf-8")
        (adr_dir / "README.md").write_text("# ADR Index", encoding="utf-8")

        (self.workspace / "README.md").write_text(
            "# Demo\n\n- [ADR 0001](docs/adr/0001-initial-architecture.md)\n", encoding="utf-8"
        )
        (self.workspace / "spec.md").write_text("# Spec\n\nReferencing ADR 0001", encoding="utf-8")

    def test_valid_workspace_passes_release_check(self) -> None:
        self._setup_valid_workspace()
        report: ReleaseReadinessReport = check_release_readiness(self.workspace)
        self.assertTrue(report.is_ready)
        self.assertEqual(report.declared_version, "0.4.0")
        self.assertEqual(len(report.diagnostics), 0)

    def test_changelog_missing_version_entry_fails(self) -> None:
        self._setup_valid_workspace()
        (self.workspace / "CHANGELOG.md").write_text(
            "# Changelog\n\n## [0.3.0] - 2026-08-20\n- Old notes\n", encoding="utf-8"
        )
        report = check_release_readiness(self.workspace)
        self.assertFalse(report.is_ready)
        self.assertTrue(
            any("CHANGELOG_VERSION_MISMATCH" == d.tool_name for d in report.diagnostics)
        )

    def test_package_json_version_mismatch_fails(self) -> None:
        self._setup_valid_workspace()
        pkg_json = self.workspace / "packages" / "demo-pkg" / "package.json"
        pkg_json.write_text('{"name": "demo-pkg", "version": "0.3.9"}', encoding="utf-8")
        report = check_release_readiness(self.workspace)
        self.assertFalse(report.is_ready)
        self.assertTrue(any("CONFIG_VERSION_MISMATCH" == d.tool_name for d in report.diagnostics))

    def test_unreferenced_adr_in_docs_fails(self) -> None:
        self._setup_valid_workspace()
        adr_dir = self.workspace / "docs" / "adr"
        (adr_dir / "0002-missing-adr.md").write_text("# ADR 0002", encoding="utf-8")
        report = check_release_readiness(self.workspace)
        self.assertFalse(report.is_ready)
        self.assertTrue(any("UNREFERENCED_ADR" == d.tool_name for d in report.diagnostics))

    def test_allow_unreleased_flag_accepts_unreleased_changelog(self) -> None:
        self._setup_valid_workspace()
        (self.workspace / "CHANGELOG.md").write_text(
            "# Changelog\n\n## [Unreleased]\n- Work in progress\n\n## [0.3.0] - 2026-08-20\n",
            encoding="utf-8",
        )
        report_strict = check_release_readiness(self.workspace, allow_unreleased=False)
        self.assertFalse(report_strict.is_ready)

        report_allow = check_release_readiness(self.workspace, allow_unreleased=True)
        self.assertTrue(report_allow.is_ready)

    def test_cli_check_release_command_success(self) -> None:
        self._setup_valid_workspace()
        code = main(["check-release", "--workspace", str(self.workspace)])
        self.assertEqual(code, 0)

    def test_cli_check_release_command_failure_and_json_output(self) -> None:
        self._setup_valid_workspace()
        (self.workspace / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
        code = main(["check-release", "--workspace", str(self.workspace), "--json"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
