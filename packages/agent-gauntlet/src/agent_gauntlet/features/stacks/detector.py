"""Stack auto-detector based on workspace indicator markers and TypeScript config inspection."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _strip_json_comments_and_trailing_commas(text: str) -> str:
    """Strips block comments, line comments, and trailing commas from JSONC text."""
    # 1. Remove multi-line comments /* ... */
    no_block_comments = re.sub(r"/\*[\s\S]*?\*/", "", text)
    # 2. Remove single-line comments // ...
    no_line_comments = re.sub(r"//.*$", "", no_block_comments, flags=re.MULTILINE)
    # 3. Remove trailing commas before } or ]
    clean_json = re.sub(r",\s*([\]}])", r"\1", no_line_comments)
    return clean_json.strip()


def inspect_typescript_tsconfig(tsconfig_path: Path) -> dict[str, Any] | None:
    """Parses a tsconfig.json file safely, tolerating JSONC comments and trailing commas."""
    if not tsconfig_path.is_file():
        return None

    try:
        raw_text = tsconfig_path.read_text(encoding="utf-8")
        clean_text = _strip_json_comments_and_trailing_commas(raw_text)
        data = json.loads(clean_text)
        if isinstance(data, dict):
            return data
    except Exception:
        # Fallback: heuristics if malformed JSON
        try:
            raw_text = tsconfig_path.read_text(encoding="utf-8", errors="ignore")
            if re.search(r'"references"\s*:\s*\[', raw_text):
                return {"references": [{"path": "detected"}]}
        except Exception:
            return None

    return None


def has_typescript_project_references(workspace_path: Path | str) -> bool:
    """Checks if a workspace uses TypeScript Project References or Solution Style tsconfig."""
    root = Path(workspace_path).resolve()
    tsconfig_p = root / "tsconfig.json"

    if tsconfig_p.is_file():
        data = inspect_typescript_tsconfig(tsconfig_p)
        if data and isinstance(data.get("references"), list) and len(data["references"]) > 0:
            return True

    if (root / "tsconfig.app.json").is_file() or (root / "tsconfig.node.json").is_file():
        return True

    return False


def get_typescript_typecheck_command(workspace_path: Path | str | None = None) -> list[str]:
    """Determines the authoritative TypeScript typecheck command for a given workspace.

    - Returns ['npx', 'tsc', '-b'] if tsconfig.json uses Project References (Solution style).
    - Returns ['npx', 'tsc', '--noEmit', '-p', 'tsconfig.app.json'] if tsconfig.app.json exists without root references.
    - Returns ['npx', 'tsc', '--noEmit'] for standard single tsconfig.
    """
    if workspace_path is None:
        return ["npx", "tsc", "--noEmit"]

    root = Path(workspace_path).resolve()
    tsconfig_p = root / "tsconfig.json"

    if tsconfig_p.is_file():
        data = inspect_typescript_tsconfig(tsconfig_p)
        if data and isinstance(data.get("references"), list) and len(data["references"]) > 0:
            return ["npx", "tsc", "-b"]

        if (root / "tsconfig.app.json").is_file():
            return ["npx", "tsc", "--noEmit", "-p", "tsconfig.app.json"]

        return ["npx", "tsc", "--noEmit"]

    if (root / "tsconfig.app.json").is_file():
        return ["npx", "tsc", "--noEmit", "-p", "tsconfig.app.json"]

    return ["npx", "tsc", "--noEmit"]


PYTHON_MARKERS = (
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "uv.lock",
    "environment.yml",
)

SCAN_SUBDIRS = (
    "frontend",
    "backend",
    "web",
    "api",
    "client",
    "server",
    "apps",
    "packages",
    "services",
    "crates",
    "src",
    "wasm",
    "rust",
    "native",
    "src-wasm",
    "core",
)


def _detect_stack_in_dir(directory: Path) -> str | None:
    """Detects stack marker in a specific directory."""
    if not directory.is_dir():
        return None

    if (directory / "Cargo.toml").exists():
        return "rust"

    if (directory / "tsconfig.json").exists() or (directory / "package.json").exists():
        return "typescript"

    for marker in PYTHON_MARKERS:
        if (directory / marker).exists():
            return "python"

    return None


def detect_stacks(workspace_path: Path | str) -> list[str]:
    """Detects all programming stacks in a workspace across root and subdirectories."""
    root = Path(workspace_path).resolve()
    if not root.is_dir():
        return []

    detected: list[str] = []

    def _add_stack(stack: str | None) -> None:
        if stack and stack not in detected:
            detected.append(stack)

    # 1. Root inspection
    _add_stack(_detect_stack_in_dir(root))

    # 2. Subdirectory inspection
    for sub in SCAN_SUBDIRS:
        sub_path = root / sub
        if not sub_path.is_dir():
            continue
        _add_stack(_detect_stack_in_dir(sub_path))

        # Check 1 level deeper for container folders (e.g. apps/*, packages/*, services/*, crates/*, wasm/*)
        if sub in ("apps", "packages", "services", "crates", "wasm", "rust", "native"):
            try:
                for child in sub_path.iterdir():
                    if child.is_dir():
                        _add_stack(_detect_stack_in_dir(child))
            except OSError:
                pass

    return detected


def detect_stack(workspace_path: Path | str) -> str | None:
    """Detect programming stack of a workspace by checking standard project indicator files."""
    stacks = detect_stacks(workspace_path)
    return stacks[0] if stacks else None
