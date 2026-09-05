"""Safe Project Scaffolding feature for agent-gauntlet."""

from agent_gauntlet.features.scaffold.models import ScaffoldEntry, ScaffoldResult, ScaffoldStatus
from agent_gauntlet.features.scaffold.prompt import prompt_for_stack, resolve_scaffold_stack
from agent_gauntlet.features.scaffold.scaffolder import ProjectScaffolder

__all__ = [
    "ProjectScaffolder",
    "ScaffoldEntry",
    "ScaffoldResult",
    "ScaffoldStatus",
    "prompt_for_stack",
    "resolve_scaffold_stack",
]
