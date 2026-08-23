"""Vertical slice harness adapters for agent-gauntlet."""

from __future__ import annotations

from agent_gauntlet.features.adapters.antigravity import AntigravityAdapter
from agent_gauntlet.features.adapters.models import (
    AdapterHookVerdict,
    AdapterValidationResult,
    HarnessAdapterProtocol,
    NormalizedToolCall,
    ToolActionType,
    ValidationIssue,
    ValidationSeverity,
)

SUPPORTED_HARNESSES: list[str] = [
    "antigravity",
]


def get_adapter(harness_name: str) -> HarnessAdapterProtocol:
    """Returns the adapter instance corresponding to the specified harness name."""
    normalized = harness_name.strip().lower()
    if normalized == "antigravity":
        return AntigravityAdapter()

    raise ValueError(
        f"Unsupported harness '{harness_name}'. Supported harnesses: {', '.join(SUPPORTED_HARNESSES)}"
    )


__all__ = [
    "SUPPORTED_HARNESSES",
    "AdapterHookVerdict",
    "AdapterValidationResult",
    "AntigravityAdapter",
    "HarnessAdapterProtocol",
    "NormalizedToolCall",
    "ToolActionType",
    "ValidationIssue",
    "ValidationSeverity",
    "get_adapter",
]
