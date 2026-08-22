"""Stack auto-detector based on workspace indicator markers."""

from __future__ import annotations

from pathlib import Path


def detect_stack(workspace_path: Path | str) -> str | None:
    """Detect programming stack of a workspace by checking standard project indicator files."""
    root = Path(workspace_path).resolve()

    # 1. Rust indicator: Cargo.toml
    if (root / "Cargo.toml").exists():
        return "rust"

    # 2. TypeScript / JavaScript indicators: tsconfig.json or package.json
    if (root / "tsconfig.json").exists() or (root / "package.json").exists():
        return "typescript"

    # 3. Python indicators: pyproject.toml, requirements.txt, setup.py, Pipfile, uv.lock
    python_markers = [
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "setup.cfg",
        "Pipfile",
        "uv.lock",
        "environment.yml",
    ]
    for marker in python_markers:
        if (root / marker).exists():
            return "python"

    return None
