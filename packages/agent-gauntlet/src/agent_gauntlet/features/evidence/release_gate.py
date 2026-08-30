"""Automated Release Readiness and Documentation Synchronization Gate.

Verifies version consistency across configs, CHANGELOG.md release notes,
and ADR documentation coverage before software release.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent_gauntlet.features.diagnostics.models import DiagnosticFinding, FindingType


@dataclass(frozen=True)
class ReleaseReadinessReport:
    """Consolidated assessment of repository release readiness and documentation sync."""

    is_ready: bool
    declared_version: str
    diagnostics: list[DiagnosticFinding] = field(default_factory=list)
    inspected_files: list[str] = field(default_factory=list)
    versions_by_source: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serializes the report to a dictionary for CLI or JSON consumption."""
        return {
            "is_ready": self.is_ready,
            "declared_version": self.declared_version,
            "versions_by_source": self.versions_by_source,
            "inspected_files": self.inspected_files,
            "diagnostics": [
                {
                    "file_path": d.file_path,
                    "category": d.tool_name,
                    "message": d.message,
                    "remediation_hint": d.remediation_hint,
                }
                for d in self.diagnostics
            ],
        }


class ReleaseReadinessEngine:
    """Evaluates workspace release readiness against documentation and versioning rules."""

    def extract_declared_versions(self, workspace: Path) -> tuple[dict[str, str], list[str]]:
        """Extracts version strings declared across project manifest files.

        Args:
            workspace: Root directory of the repository workspace.

        Returns:
            Tuple of (versions_by_source dict, list of inspected file paths).
        """
        versions: dict[str, str] = {}
        inspected: list[str] = []

        # 1. pyproject.toml
        pyproject = workspace / "pyproject.toml"
        if pyproject.is_file():
            inspected.append("pyproject.toml")
            content = pyproject.read_text(encoding="utf-8")
            match = re.search(r'(?m)^\s*version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                versions["pyproject.toml"] = match.group(1).strip()

        # 2. Root or packages/*/package.json
        pkg_files = [workspace / "package.json"] + list(workspace.glob("packages/*/package.json"))
        for pkg_file in pkg_files:
            if pkg_file.is_file():
                rel_path = str(pkg_file.relative_to(workspace)).replace("\\", "/")
                inspected.append(rel_path)
                try:
                    data = json.loads(pkg_file.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and "version" in data and data["version"]:
                        versions[rel_path] = str(data["version"]).strip()
                except Exception:
                    pass

        # 3. Cargo.toml
        cargo = workspace / "Cargo.toml"
        if cargo.is_file():
            inspected.append("Cargo.toml")
            content = cargo.read_text(encoding="utf-8")
            match = re.search(r'(?m)^\s*version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                versions["Cargo.toml"] = match.group(1).strip()

        return versions, inspected

    def parse_changelog_versions(self, changelog_path: Path) -> list[str]:
        """Parses release version headers from a Keep a Changelog markdown file.

        Args:
            changelog_path: Path to CHANGELOG.md file.

        Returns:
            List of parsed version header strings (e.g. ['0.4.0', '0.3.0', 'Unreleased']).
        """
        if not changelog_path.is_file():
            return []
        content = changelog_path.read_text(encoding="utf-8")
        headers: list[str] = []
        for line in content.splitlines():
            match = re.match(r"^##\s*\[([^\]]+)\]", line.strip())
            if match:
                headers.append(match.group(1).strip())
        return headers

    def check_adr_references(self, workspace: Path) -> tuple[list[DiagnosticFinding], list[str]]:
        """Verifies that all Architecture Decision Records in docs/adr/ are referenced.

        Args:
            workspace: Root directory of the repository workspace.

        Returns:
            Tuple of (list of DiagnosticFinding, list of inspected adr paths).
        """
        diagnostics: list[DiagnosticFinding] = []
        inspected_adrs: list[str] = []
        adr_dir = workspace / "docs" / "adr"
        if not adr_dir.is_dir():
            return diagnostics, inspected_adrs

        readme_file = workspace / "README.md"
        spec_file = workspace / "spec.md"
        readme_content = readme_file.read_text(encoding="utf-8") if readme_file.is_file() else ""
        spec_content = spec_file.read_text(encoding="utf-8") if spec_file.is_file() else ""
        combined_doc = readme_content + "\n" + spec_content

        for adr_path in sorted(adr_dir.glob("*.md")):
            if adr_path.name.lower() in ("readme.md", "index.md"):
                continue
            rel_adr = str(adr_path.relative_to(workspace)).replace("\\", "/")
            inspected_adrs.append(rel_adr)

            # Check if referenced either by file name, relative path, or ADR number
            adr_stem = adr_path.stem
            adr_num_match = re.match(r"^(\d+)", adr_path.name)
            adr_num = adr_num_match.group(1) if adr_num_match else ""

            is_referenced = (
                adr_path.name in combined_doc
                or rel_adr in combined_doc
                or (adr_num and f"ADR {int(adr_num)}" in combined_doc)
                or (adr_num and f"ADR {adr_num}" in combined_doc)
                or adr_stem in combined_doc
            )

            if not is_referenced:
                diagnostics.append(
                    DiagnosticFinding(
                        finding_type=FindingType.GENERAL_ERROR,
                        tool_name="UNREFERENCED_ADR",
                        file_path=rel_adr,
                        message=f"Architecture Decision Record '{adr_path.name}' is not referenced in README.md or spec.md.",
                        remediation_hint=f"Add a link to [{adr_path.name}]({rel_adr}) in README.md and spec.md.",
                    )
                )

        return diagnostics, inspected_adrs

    def evaluate(
        self,
        workspace: Path,
        allow_unreleased: bool = False,
    ) -> ReleaseReadinessReport:
        """Executes full release readiness validation.

        Args:
            workspace: Root workspace path.
            allow_unreleased: If True, allows 'Unreleased' in CHANGELOG.md instead of strict version match.

        Returns:
            A ReleaseReadinessReport detailing readiness verdict and any actionable diagnostics.
        """
        diagnostics: list[DiagnosticFinding] = []
        versions_by_source, inspected_files = self.extract_declared_versions(workspace)

        # 1. Determine target release version
        unique_versions = set(versions_by_source.values())
        if not unique_versions:
            declared_version = "0.0.0"
        elif len(unique_versions) > 1:
            declared_version = next(iter(unique_versions))
            mismatch_details = ", ".join(f"{k}: {v}" for k, v in versions_by_source.items())
            diagnostics.append(
                DiagnosticFinding(
                    finding_type=FindingType.GENERAL_ERROR,
                    tool_name="CONFIG_VERSION_MISMATCH",
                    file_path=inspected_files[0] if inspected_files else "pyproject.toml",
                    message=f"Version mismatch detected across project manifests: {mismatch_details}.",
                    remediation_hint="Synchronize version numbers across all package manifest files.",
                )
            )
        else:
            declared_version = next(iter(unique_versions))

        # 2. Check CHANGELOG.md
        changelog_path = workspace / "CHANGELOG.md"
        if not changelog_path.is_file():
            diagnostics.append(
                DiagnosticFinding(
                    finding_type=FindingType.GENERAL_ERROR,
                    tool_name="MISSING_CHANGELOG",
                    file_path="CHANGELOG.md",
                    message="Missing 'CHANGELOG.md' in workspace root.",
                    remediation_hint="Create a CHANGELOG.md following Keep a Changelog specification.",
                )
            )
        else:
            inspected_files.append("CHANGELOG.md")
            changelog_versions = self.parse_changelog_versions(changelog_path)
            has_matching_version = declared_version in changelog_versions
            has_unreleased = any(v.lower() == "unreleased" for v in changelog_versions)

            if not has_matching_version:
                if allow_unreleased and has_unreleased:
                    pass  # Allowed in advisory / dev mode
                else:
                    diagnostics.append(
                        DiagnosticFinding(
                            finding_type=FindingType.GENERAL_ERROR,
                            tool_name="CHANGELOG_VERSION_MISMATCH",
                            file_path="CHANGELOG.md",
                            message=(
                                f"CHANGELOG.md does not contain an entry for declared release version '{declared_version}'. "
                                f"Found versions: {changelog_versions}."
                            ),
                            remediation_hint=(
                                f"Add a '## [{declared_version}] - YYYY-MM-DD' section to CHANGELOG.md "
                                f"with release notes before publishing."
                            ),
                        )
                    )

        # 3. Check ADR coverage in README.md & spec.md
        adr_diagnostics, inspected_adrs = self.check_adr_references(workspace)
        diagnostics.extend(adr_diagnostics)
        inspected_files.extend(inspected_adrs)

        is_ready = len(diagnostics) == 0
        return ReleaseReadinessReport(
            is_ready=is_ready,
            declared_version=declared_version,
            diagnostics=diagnostics,
            inspected_files=inspected_files,
            versions_by_source=versions_by_source,
        )


def check_release_readiness(
    workspace: Path,
    allow_unreleased: bool = False,
) -> ReleaseReadinessReport:
    """Convenience functional helper evaluating release readiness.

    Args:
        workspace: Path to workspace root.
        allow_unreleased: If True, allows '[Unreleased]' changelog section.

    Returns:
        ReleaseReadinessReport instance.
    """
    engine = ReleaseReadinessEngine()
    return engine.evaluate(workspace, allow_unreleased=allow_unreleased)
