"""Default verification layer profiles for supported Tier-1 stacks."""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from agent_gauntlet.features.gauntlet.models import LayerDefinition
from agent_gauntlet.features.stacks.detector import get_typescript_typecheck_command

SUPPORTED_STACKS: Sequence[str] = ("python", "typescript", "rust")


def get_python_default_layers() -> list[LayerDefinition]:
    """Generate default verification layers for a Python project."""
    return [
        LayerDefinition(
            name="lint",
            command=[sys.executable, "-m", "ruff", "check", "."],
            optional=True,
            timeout_seconds=30.0,
        ),
        LayerDefinition(
            name="types",
            command=[sys.executable, "-m", "pyright", "src", "tests", "tools"],
            optional=True,
            timeout_seconds=60.0,
        ),
        LayerDefinition(
            name="unit",
            command=[sys.executable, "-m", "unittest", "discover", "tests"],
            optional=False,
            timeout_seconds=60.0,
        ),
        LayerDefinition(
            name="invariants",
            command=[
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-p",
                "*propert*.py",
            ],
            optional=True,
            timeout_seconds=60.0,
        ),
        LayerDefinition(
            name="mutation-testing-gauntlet",
            command=[sys.executable, "tools/mutants.py"],
            optional=True,
            timeout_seconds=120.0,
        ),
    ]


def get_typescript_default_layers(
    workspace_path: Path | str | None = None,
) -> list[LayerDefinition]:
    """Generate default verification layers for a TypeScript project."""
    typecheck_cmd = get_typescript_typecheck_command(workspace_path)
    return [
        LayerDefinition(
            name="lint",
            command=["npx", "eslint", "."],
            optional=True,
            timeout_seconds=30.0,
        ),
        LayerDefinition(
            name="types",
            command=typecheck_cmd,
            optional=True,
            timeout_seconds=60.0,
        ),
        LayerDefinition(
            name="unit",
            command=["npm", "test"],
            optional=False,
            timeout_seconds=60.0,
        ),
        LayerDefinition(
            name="invariants",
            command=["npm", "run", "test:invariants"],
            optional=True,
            timeout_seconds=60.0,
        ),
        LayerDefinition(
            name="mutation-testing-gauntlet",
            command=["npx", "stryker", "run"],
            optional=True,
            timeout_seconds=120.0,
        ),
    ]


def get_rust_default_layers() -> list[LayerDefinition]:
    """Generate default verification layers for a Rust project."""
    return [
        LayerDefinition(
            name="lint",
            command=["cargo", "clippy", "--", "-D", "warnings"],
            optional=True,
            timeout_seconds=60.0,
        ),
        LayerDefinition(
            name="types",
            command=["cargo", "check"],
            optional=True,
            timeout_seconds=60.0,
        ),
        LayerDefinition(
            name="unit",
            command=["cargo", "test"],
            optional=False,
            timeout_seconds=120.0,
        ),
        LayerDefinition(
            name="invariants",
            command=["cargo", "test", "--", "proptest"],
            optional=True,
            timeout_seconds=120.0,
        ),
        LayerDefinition(
            name="mutation-testing-gauntlet",
            command=["cargo", "mutants"],
            optional=True,
            timeout_seconds=180.0,
        ),
    ]


STACK_PROFILE_GENERATORS: Mapping[str, Callable[[], list[LayerDefinition]]] = {
    "python": get_python_default_layers,
    "typescript": get_typescript_default_layers,
    "rust": get_rust_default_layers,
}


def get_default_stack_profile(
    stack_name: str,
    workspace_path: Path | str | None = None,
) -> list[LayerDefinition]:
    """Retrieve default verification layers for given stack name and optional workspace context."""
    normalized = stack_name.lower().strip()
    if normalized == "typescript":
        return get_typescript_default_layers(workspace_path)

    generator = STACK_PROFILE_GENERATORS.get(normalized)
    if not generator:
        raise ValueError(
            f"Unsupported stack '{stack_name}'. Supported stacks are: {', '.join(SUPPORTED_STACKS)}"
        )
    return generator()
