"""Mechanical rules and configuration validator for Cursor IDE."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agent_gauntlet.features.adapters.models import (
    AdapterValidationResult,
    ValidationIssue,
    ValidationSeverity,
)


class CursorRulesValidator:
    """Mechanically validates Cursor rules (.cursor/rules/*.mdc) and configuration."""

    def _parse_frontmatter(self, content: str) -> tuple[dict[str, Any] | None, str | None]:
        """Extracts YAML frontmatter from an MDC rule file.

        Args:
            content: Raw text content of the rule file.

        Returns:
            Tuple of (metadata_dict, error_message).
        """
        if not content.startswith("---"):
            return None, "File does not start with '---' YAML frontmatter delimiter."

        lines = content.splitlines(keepends=True)
        closing_index = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                closing_index = i
                break

        if closing_index == -1:
            return None, "Unclosed YAML frontmatter block (missing terminating '---')."

        yaml_text = "".join(lines[1:closing_index])
        try:
            data = yaml.safe_load(yaml_text)
            if data is None:
                return {}, None
            if not isinstance(data, dict):
                return None, f"Frontmatter must parse to a mapping, got {type(data).__name__}."
            return data, None
        except Exception as exc:
            return None, f"Invalid YAML frontmatter: {exc}"

    def _validate_rule_file(
        self,
        rule_path: Path,
        rel_path: str,
        issues: list[ValidationIssue],
    ) -> None:
        """Validates a single Cursor MDC rule file.

        Args:
            rule_path: Absolute or resolved path to the rule file.
            rel_path: Relative display path for error reporting.
            issues: Mutable list to accumulate validation findings.
        """
        try:
            content = rule_path.read_text(encoding="utf-8")
        except Exception as exc:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=rel_path,
                    message=f"Failed to read rule file: {exc}",
                )
            )
            return

        meta, parse_err = self._parse_frontmatter(content)
        if parse_err or meta is None:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=rel_path,
                    message=parse_err or "Missing YAML frontmatter in rule file.",
                )
            )
            return

        # 1. Description validation
        description = meta.get("description")
        if not description or not isinstance(description, str) or not description.strip():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=rel_path,
                    message="Rule frontmatter is missing required non-empty string 'description'.",
                )
            )

        # 2. Globs validation
        globs = meta.get("globs")
        if globs is None or (isinstance(globs, str) and not globs.strip()):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=rel_path,
                    message="Rule frontmatter is missing required 'globs' pattern.",
                )
            )

        # 3. alwaysApply validation
        always_apply = meta.get("alwaysApply")
        if always_apply is None:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=rel_path,
                    message="Rule frontmatter is missing required boolean property 'alwaysApply'.",
                )
            )
        elif not isinstance(always_apply, bool):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=rel_path,
                    message=f"'alwaysApply' must be a boolean (true/false), got {type(always_apply).__name__}.",
                )
            )

    def validate(self, target_dir: Path) -> AdapterValidationResult:
        """Validates all Cursor rule files in the given directory or workspace.

        Args:
            target_dir: Workspace root or .cursor directory.

        Returns:
            AdapterValidationResult with issues and validity status.
        """
        issues: list[ValidationIssue] = []

        # Find .mdc rule files in target_dir or target_dir/.cursor/rules
        rule_files: list[Path] = []
        if target_dir.is_file() and target_dir.suffix.lower() == ".mdc":
            rule_files.append(target_dir)
        elif target_dir.is_dir():
            rules_subdir = target_dir / ".cursor/rules"
            if rules_subdir.is_dir():
                rule_files.extend(sorted(rules_subdir.glob("*.mdc")))
            elif (target_dir / "rules").is_dir():
                rule_files.extend(sorted((target_dir / "rules").glob("*.mdc")))
            else:
                rule_files.extend(sorted(target_dir.glob("*.mdc")))

        if not rule_files:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=str(target_dir),
                    message="No Cursor rule (.mdc) files found in directory.",
                )
            )
            return AdapterValidationResult(valid=False, issues=issues)

        for rf in rule_files:
            try:
                rel = str(rf.relative_to(target_dir))
            except ValueError:
                rel = str(rf)
            self._validate_rule_file(rf, rel, issues)

        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
        return AdapterValidationResult(valid=not has_errors, issues=issues)
