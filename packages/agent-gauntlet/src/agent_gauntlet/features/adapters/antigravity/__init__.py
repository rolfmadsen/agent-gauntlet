"""Google Antigravity IDE adapter vertical slice."""

from agent_gauntlet.features.adapters.antigravity.adapter import AntigravityAdapter
from agent_gauntlet.features.adapters.antigravity.hook import main_hook_entrypoint
from agent_gauntlet.features.adapters.antigravity.validator import AntigravityPluginValidator

__all__ = [
    "AntigravityAdapter",
    "AntigravityPluginValidator",
    "main_hook_entrypoint",
]
