"""Mechanical plugin and manifest validator for Google Antigravity IDE."""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from typing import Any

from agent_gauntlet.features.adapters.models import (
    AdapterValidationResult,
    ValidationIssue,
    ValidationSeverity,
)

VALID_EVENT_TYPES = {"PreToolUse", "PostToolUse", "PreInvocation", "PostInvocation", "Stop"}


class AntigravityPluginValidator:
    """Mechanically validates an Antigravity plugin directory, manifest, skills, and official hooks.json schema."""

    def _validate_hook_handler(
        self,
        handler: Any,
        path: str,
        issues: list[ValidationIssue],
    ) -> None:
        """Validates a single hook handler object."""
        if not isinstance(handler, dict):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=path,
                    message=f"Hook handler must be an object, got {type(handler).__name__}.",
                )
            )
            return

        command = handler.get("command")
        if not command or not isinstance(command, str) or not command.strip():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=path,
                    message="Hook handler is missing required string property 'command'.",
                )
            )

        handler_type = handler.get("type", "command")
        if handler_type != "command":
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=path,
                    message=f"Unsupported hook type '{handler_type}'. Only 'command' is currently supported.",
                )
            )

        timeout = handler.get("timeout")
        if timeout is not None:
            if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        path=path,
                        message=f"'timeout' must be a positive integer, got {timeout}.",
                    )
                )

    def _validate_hooks_json(
        self,
        hooks_file: Path,
        issues: list[ValidationIssue],
    ) -> None:
        """Validates hooks.json against the official Google Antigravity Lifecycle Hooks schema."""
        try:
            data = json.loads(hooks_file.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path="hooks.json",
                    message=f"Invalid JSON in 'hooks.json': {exc}",
                )
            )
            return

        if not isinstance(data, dict):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path="hooks.json",
                    message="'hooks.json' root must be a JSON object mapping hook names to configurations.",
                )
            )
            return

        if not data:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path="hooks.json",
                    message="'hooks.json' root object cannot be empty. Must define at least one named hook.",
                )
            )
            return

        # Check if root accidentally uses flat/legacy format
        legacy_keys = {"pre_tool_invocation", "command", "hooks", "PreToolUse", "PostToolUse"}
        if any(k in legacy_keys for k in data.keys()) and not any(
            isinstance(v, dict) and any(ev in v for ev in VALID_EVENT_TYPES) for v in data.values()
        ):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path="hooks.json",
                    message=(
                        "Non-conforming root format in 'hooks.json'. The official Antigravity schema requires "
                        "named hook objects at root, e.g., {'my-hook': {'PreToolUse': [...]}}."
                    ),
                )
            )
            return

        for hook_name, hook_config in data.items():
            if not isinstance(hook_config, dict):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        path="hooks.json",
                        message=f"Configuration for hook '{hook_name}' must be an object.",
                    )
                )
                continue

            enabled = hook_config.get("enabled", True)
            if not isinstance(enabled, bool):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        path="hooks.json",
                        message=f"'enabled' in hook '{hook_name}' must be a boolean.",
                    )
                )

            event_keys = [k for k in hook_config.keys() if k != "enabled"]
            if not event_keys:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        path="hooks.json",
                        message=f"Hook '{hook_name}' must define at least one lifecycle event from {sorted(VALID_EVENT_TYPES)}.",
                    )
                )

            for event_name, event_config in hook_config.items():
                if event_name == "enabled":
                    continue

                if event_name not in VALID_EVENT_TYPES:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            path="hooks.json",
                            message=f"Unknown lifecycle event '{event_name}' in hook '{hook_name}'. Valid events: {sorted(VALID_EVENT_TYPES)}.",
                        )
                    )
                    continue

                if not isinstance(event_config, list):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            path="hooks.json",
                            message=f"Event '{event_name}' in hook '{hook_name}' must be an array of handlers.",
                        )
                    )
                    continue

                if event_name in ("PreToolUse", "PostToolUse"):
                    for idx, matcher_group in enumerate(event_config):
                        if not isinstance(matcher_group, dict):
                            issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.ERROR,
                                    path="hooks.json",
                                    message=f"{event_name}[{idx}] in hook '{hook_name}' must be an object with 'matcher' and 'hooks'.",
                                )
                            )
                            continue

                        matcher = matcher_group.get("matcher")
                        if matcher is None or not isinstance(matcher, str):
                            issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.ERROR,
                                    path="hooks.json",
                                    message=f"{event_name}[{idx}] in hook '{hook_name}' is missing string 'matcher'.",
                                )
                            )
                        else:
                            # Antigravity supports '*' and '' as official match-all wildcards
                            if matcher not in ("*", ""):
                                try:
                                    re.compile(matcher)
                                except re.error as err:
                                    issues.append(
                                        ValidationIssue(
                                            severity=ValidationSeverity.ERROR,
                                            path="hooks.json",
                                            message=f"Invalid regex in matcher '{matcher}': {err}",
                                        )
                                    )

                        handlers_list = matcher_group.get("hooks", [])
                        if not isinstance(handlers_list, list) or len(handlers_list) == 0:
                            issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.ERROR,
                                    path="hooks.json",
                                    message=f"{event_name}[{idx}] in hook '{hook_name}' must contain a non-empty 'hooks' array.",
                                )
                            )
                        else:
                            for h_idx, handler in enumerate(handlers_list):
                                self._validate_hook_handler(
                                    handler,
                                    f"hooks.json:{hook_name}.{event_name}[{idx}].hooks[{h_idx}]",
                                    issues,
                                )
                else:
                    # Flat handler events: PreInvocation, PostInvocation, Stop
                    for idx, handler in enumerate(event_config):
                        self._validate_hook_handler(
                            handler,
                            f"hooks.json:{hook_name}.{event_name}[{idx}]",
                            issues,
                        )

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

        # 4. Validate hooks.json against official schema
        hooks_file = plugin_dir / "hooks.json"
        if hooks_file.is_file():
            self._validate_hooks_json(hooks_file, issues)

        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
        return AdapterValidationResult(valid=not has_errors, issues=issues)
