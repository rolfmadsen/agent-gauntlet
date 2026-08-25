"""Mechanical plugin and manifest validator for Google Antigravity IDE."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

from agent_gauntlet.features.adapters.models import (
    AdapterValidationResult,
    ValidationIssue,
    ValidationSeverity,
)


class AntigravityPluginValidator:
    """Mechanically validates an Antigravity plugin directory, manifest, skills, and hooks."""

    def validate(self, plugin_dir: Path) -> AdapterValidationResult:
        """Validates all plugin components in the given plugin directory."""
        issues: list[ValidationIssue] = []

        if not plugin_dir.is_dir():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=str(plugin_dir),
                    message=f"Plugin directory '{plugin_dir}' does not exist.",
                )
            )
            return AdapterValidationResult(valid=False, issues=issues)

        # 1. Validate plugin.json
        manifest_file = plugin_dir / "plugin.json"
        manifest_data: dict = {}
        if not manifest_file.is_file():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path="plugin.json",
                    message="Missing required manifest file 'plugin.json'.",
                )
            )
        else:
            try:
                manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
                if not isinstance(manifest_data, dict):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            path="plugin.json",
                            message="'plugin.json' must be a JSON object.",
                        )
                    )
                    manifest_data = {}
            except Exception as exc:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        path="plugin.json",
                        message=f"Invalid JSON in 'plugin.json': {exc}",
                    )
                )

        if manifest_data:
            if not manifest_data.get("name"):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        path="plugin.json",
                        message="Missing required field 'name' in 'plugin.json'.",
                    )
                )
            if not manifest_data.get("version"):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        path="plugin.json",
                        message="Missing required field 'version' in 'plugin.json'.",
                    )
                )

            # 2. Validate Skills declared in manifest
            declared_skills = manifest_data.get("skills", [])
            if isinstance(declared_skills, list):
                for skill_name in declared_skills:
                    skill_file = plugin_dir / "skills" / skill_name / "SKILL.md"
                    if not skill_file.is_file():
                        issues.append(
                            ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                path=f"skills/{skill_name}/SKILL.md",
                                message=f"Declared skill '{skill_name}' is missing 'SKILL.md' file.",
                            )
                        )
                    else:
                        try:
                            content = skill_file.read_text(encoding="utf-8")
                            has_frontmatter = (
                                content.startswith("---")
                                and "name:" in content
                                and "description:" in content
                            )
                            if not has_frontmatter:
                                issues.append(
                                    ValidationIssue(
                                        severity=ValidationSeverity.ERROR,
                                        path=f"skills/{skill_name}/SKILL.md",
                                        message=f"Skill '{skill_name}' is missing valid YAML frontmatter (name, description).",
                                    )
                                )
                        except Exception as exc:
                            issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.ERROR,
                                    path=f"skills/{skill_name}/SKILL.md",
                                    message=f"Could not read skill file '{skill_file}': {exc}",
                                )
                            )

            # 3. Validate Entrypoints declared in manifest
            entrypoints = manifest_data.get("entrypoints", {})
            if isinstance(entrypoints, dict):
                for ep_name, ep_target in entrypoints.items():
                    if not isinstance(ep_target, str) or not ep_target:
                        issues.append(
                            ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                path="plugin.json",
                                message=f"Entrypoint '{ep_name}' has invalid target format.",
                            )
                        )
                        continue

                    target_str = str(ep_target).strip()
                    module_part, _, attr_part = target_str.partition(":")
                    try:
                        mod = importlib.import_module(module_part)
                        if attr_part and not hasattr(mod, attr_part):
                            issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.ERROR,
                                    path="plugin.json",
                                    message=f"Entrypoint '{ep_name}' references missing attribute '{attr_part}' in module '{module_part}'.",
                                )
                            )
                    except Exception as exc:
                        issues.append(
                            ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                path="plugin.json",
                                message=f"Entrypoint '{ep_name}' failed to resolve target '{ep_target}': {exc}",
                            )
                        )

        # 4. Validate hooks.json if present
        hooks_file = plugin_dir / "hooks.json"
        if hooks_file.is_file():
            try:
                hooks_data = json.loads(hooks_file.read_text(encoding="utf-8"))
                if not isinstance(hooks_data, dict):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            path="hooks.json",
                            message="'hooks.json' must be a JSON object.",
                        )
                    )
            except Exception as exc:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        path="hooks.json",
                        message=f"Invalid JSON in 'hooks.json': {exc}",
                    )
                )

        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
        return AdapterValidationResult(valid=not has_errors, issues=issues)
