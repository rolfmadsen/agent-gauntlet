"""agent-gauntlet: High-assurance multi-stack verification engine and actionable diagnostics harness."""

from agent_gauntlet.features.config import GauntletConfig, LayerConfig, load_config
from agent_gauntlet.features.diagnostics import (
    DiagnosticFinding,
    DiagnosticParser,
    DiagnosticReport,
    FindingType,
)
from agent_gauntlet.features.evidence import (
    CheckSummary,
    EvidenceAuthority,
    EvidenceRecord,
)
from agent_gauntlet.features.gauntlet import (
    GauntletReport,
    LayerDefinition,
    LayerResult,
    run_gauntlet,
)
from agent_gauntlet.features.stacks import detect_stack, get_default_stack_profile

__version__ = "0.7.0"


__all__ = [
    "CheckSummary",
    "DiagnosticFinding",
    "DiagnosticParser",
    "DiagnosticReport",
    "EvidenceAuthority",
    "EvidenceRecord",
    "FindingType",
    "GauntletConfig",
    "GauntletReport",
    "LayerConfig",
    "LayerDefinition",
    "LayerResult",
    "detect_stack",
    "get_default_stack_profile",
    "load_config",
    "run_gauntlet",
]
