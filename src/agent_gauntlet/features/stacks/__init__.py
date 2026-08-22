"""Multi-stack discovery and default profile definitions."""

from agent_gauntlet.features.stacks.detector import detect_stack
from agent_gauntlet.features.stacks.profiles import (
    SUPPORTED_STACKS,
    get_default_stack_profile,
    get_python_default_layers,
    get_rust_default_layers,
    get_typescript_default_layers,
)

__all__ = [
    "SUPPORTED_STACKS",
    "detect_stack",
    "get_default_stack_profile",
    "get_python_default_layers",
    "get_rust_default_layers",
    "get_typescript_default_layers",
]
