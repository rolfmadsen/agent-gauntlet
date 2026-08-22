"""Configuration loader for gauntlet.toml, gauntlet.json, and auto-discovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

from agent_gauntlet.features.config.schema import GauntletConfig, LayerConfig
from agent_gauntlet.features.stacks.detector import detect_stack
from agent_gauntlet.features.stacks.profiles import get_default_stack_profile


def _parse_dict_config(data: dict[str, Any], fallback_stack: str = "python") -> GauntletConfig:
    """Parse dictionary data into GauntletConfig."""
    stack = str(data.get("stack", fallback_stack))
    save_evidence = bool(data.get("save_evidence", True))
    evidence_file = str(data.get("evidence_file", "evidence.json"))
    evidence_markdown_file = str(data.get("evidence_markdown_file", "evidence.md"))

    layers_raw = data.get("layers", [])
    layers: list[LayerConfig] = []
    for l_data in layers_raw:
        layers.append(
            LayerConfig(
                name=str(l_data["name"]),
                command=l_data["command"],
                optional=bool(l_data.get("optional", False)),
                timeout_seconds=float(l_data.get("timeout_seconds", 60.0)),
            )
        )

    # If no layers specified, fallback to default stack profile
    if not layers:
        default_layers = get_default_stack_profile(stack)
        layers = [
            LayerConfig(
                name=l.name,
                command=l.command,
                optional=l.optional,
                timeout_seconds=l.timeout_seconds,
            )
            for l in default_layers
        ]

    return GauntletConfig(
        stack=stack,
        save_evidence=save_evidence,
        evidence_file=evidence_file,
        evidence_markdown_file=evidence_markdown_file,
        layers=layers,
    )


def load_config(
    workspace_path: Path | str,
    explicit_stack: str | None = None,
) -> GauntletConfig:
    """
    Load gauntlet configuration from workspace.
    Priority:
    1. gauntlet.toml in workspace root
    2. gauntlet.json in workspace root
    3. Auto-detected stack profile
    """
    root = Path(workspace_path).resolve()
    toml_path = root / "gauntlet.toml"
    json_path = root / "gauntlet.json"

    detected_or_fallback = explicit_stack or detect_stack(root) or "python"

    if toml_path.exists():
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
            return _parse_dict_config(data, fallback_stack=detected_or_fallback)

    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return _parse_dict_config(data, fallback_stack=detected_or_fallback)

    # Auto-detection fallback
    stack = explicit_stack or detect_stack(root) or "python"
    default_layers = get_default_stack_profile(stack)
    layers = [
        LayerConfig(
            name=l.name,
            command=l.command,
            optional=l.optional,
            timeout_seconds=l.timeout_seconds,
        )
        for l in default_layers
    ]

    return GauntletConfig(
        stack=stack,
        save_evidence=True,
        evidence_file="evidence.json",
        evidence_markdown_file="evidence.md",
        layers=layers,
    )


def generate_default_config_toml(stack: str) -> str:
    """Generate default gauntlet.toml file content for a given stack."""
    layers = get_default_stack_profile(stack)
    lines = [
        f'# agent-gauntlet configuration for {stack}',
        f'stack = "{stack}"',
        'save_evidence = true',
        'evidence_file = "evidence.json"',
        'evidence_markdown_file = "evidence.md"',
        '',
    ]
    for layer in layers:
        lines.append('[[layers]]')
        lines.append(f'name = "{layer.name}"')
        cmd_json = json.dumps(list(layer.command))
        lines.append(f'command = {cmd_json}')
        lines.append(f'optional = {"true" if layer.optional else "false"}')
        lines.append(f'timeout_seconds = {layer.timeout_seconds}')
        lines.append('')

    return '\n'.join(lines)


def generate_default_config_json(stack: str) -> str:
    """Generate default gauntlet.json file content for a given stack."""
    layers = get_default_stack_profile(stack)
    data = {
        "stack": stack,
        "save_evidence": True,
        "evidence_file": "evidence.json",
        "evidence_markdown_file": "evidence.md",
        "layers": [
            {
                "name": l.name,
                "command": list(l.command),
                "optional": l.optional,
                "timeout_seconds": l.timeout_seconds,
            }
            for l in layers
        ],
    }
    return json.dumps(data, indent=2)
