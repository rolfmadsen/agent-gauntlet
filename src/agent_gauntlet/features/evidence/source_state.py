"""Produce a deterministic, fail-closed binding for the agent-gauntlet source tree."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

SCOPES = (
    "src",
    "tests",
    "tools",
    "plugins",
    "spec.md",
    "README.md",
    "pyproject.toml",
)
EXCLUDED_DIRS = {
    ".hypothesis",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}
EXCLUDED_FILES = {".coverage", ".DS_Store", "coverage.xml"}
NO_GIT = "(no git)"
SHALLOW = "(unavailable: shallow history)"


def _git(
    root: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _is_shallow(root: Path) -> bool:
    probe = _git(root, "rev-parse", "--is-shallow-repository", check=False)
    if probe.returncode != 0:
        return True
    return os.fsdecode(probe.stdout).strip() == "true"


def _is_generated(relative: Path) -> bool:
    return (
        any(
            part in EXCLUDED_DIRS or part.endswith(".egg-info")
            for part in relative.parts
        )
        or relative.name in EXCLUDED_FILES
        or relative.suffix == ".pyc"
    )


def _manifest(root: Path) -> list[str]:
    files: list[str] = []
    for scope in SCOPES:
        candidate = root / scope
        if not candidate.exists():
            continue
        inputs = [candidate] if candidate.is_file() else candidate.rglob("*")
        scoped_files = [
            path
            for path in inputs
            if (path.is_file() or path.is_symlink())
            and not _is_generated(path.relative_to(root))
        ]
        files.extend(path.relative_to(root).as_posix() for path in scoped_files)
    return sorted(files)


def _read_input(path: Path) -> bytes:
    if path.is_symlink():
        return os.fsencode(os.readlink(path))
    if not path.is_file():
        raise RuntimeError(f"source input is not a regular file: {path}")
    try:
        return path.read_bytes()
    except OSError as error:
        raise RuntimeError(f"cannot read source input {path}: {error}") from error


def _tree_hash(root: Path, files: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in files:
        path_bytes = relative.encode("utf-8")
        content = _read_input(root / relative)
        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()[:16]


def compute_source_state(root: Path | None = None) -> tuple[str, str, str]:
    target_root = root or Path.cwd()
    files = _manifest(target_root)
    tree = _tree_hash(target_root, files)

    head_res = _git(target_root, "rev-parse", "--short", "HEAD", check=False)
    head = os.fsdecode(head_res.stdout).strip() if head_res.returncode == 0 else NO_GIT

    commit_res = _git(target_root, "log", "-1", "--format=%h", "--", *SCOPES, check=False)
    commit = os.fsdecode(commit_res.stdout).strip() if commit_res.returncode == 0 else NO_GIT

    return head, commit, tree


def main(root: Path | None = None) -> int:
    target_root = root or Path.cwd()
    try:
        head, source_commit, tree = compute_source_state(target_root)
    except Exception as error:
        print(f"source-state error: {error}", file=sys.stderr)
        return 2

    print(f"head:          {head}")
    print(f"source commit: {source_commit}")
    print(f"tree:          {tree}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
