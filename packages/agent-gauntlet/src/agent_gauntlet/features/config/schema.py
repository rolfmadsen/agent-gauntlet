"""Configuration schemas for agent-gauntlet execution and profiles."""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Sequence

from agent_gauntlet.features.gauntlet.models import LayerDefinition


@dataclass
class LayerConfig:
    """Configuration for a single verification layer in gauntlet.toml / gauntlet.json."""

    name: str
    command: Sequence[str] | str
    optional: bool = False
    timeout_seconds: float = 60.0

    def to_layer_definition(self) -> LayerDefinition:
        """Convert layer config to executable LayerDefinition."""
        if isinstance(self.command, str):
            cmd = shlex.split(self.command)
        else:
            cmd = list(self.command)
        return LayerDefinition(
            name=self.name,
            command=cmd,
            optional=self.optional,
            timeout_seconds=float(self.timeout_seconds),
        )


@dataclass
class GauntletConfig:
    """Root configuration for gauntlet execution."""

    stack: str = "python"
    save_evidence: bool = True
    evidence_file: str = "evidence.json"
    evidence_markdown_file: str = "evidence.md"
    tasks_dir: str = "tasks"
    spec_file: str = "spec.md"
    context_file: str = "CONTEXT.md"
    coding_standards_file: str = "CODING_STANDARDS.md"
    layers: list[LayerConfig] = field(default_factory=list)

    def to_layer_definitions(self) -> list[LayerDefinition]:
        """Convert all configured layers to LayerDefinitions."""
        return [layer.to_layer_definition() for layer in self.layers]
