"""Portable Canonical Workspace Snapshot generator and byte hasher."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


class SnapshotSecurityError(Exception):
    """Raised when an illegal symlink escape or snapshot security violation is detected."""


@dataclass(frozen=True)
class SnapshotEntry:
    """Individual file manifest entry with normalized relative path and byte hash."""

    path: str
    content_hash: str
    mode: int
    is_executable: bool


@dataclass(frozen=True)
class CanonicalSnapshot:
    """Deterministic, portable workspace snapshot."""

    root_digest: str
    entries: list[SnapshotEntry]


def _normalize_relative_path(rel_path: Path) -> str:
    """Normalizes a relative path to standard POSIX '/' format."""
    parts = rel_path.parts
    return "/".join(parts)


def generate_canonical_snapshot(
    workspace_root: Path,
    ignored_patterns: tuple[str, ...] = (
        ".git",
        ".venv",
        "__pycache__",
        "node_modules",
        ".ruff_cache",
        "target",
    ),
) -> CanonicalSnapshot:
    """Generates a portable, canonical snapshot of workspace files.

    Args:
        workspace_root: Absolute or relative path to workspace root.
        ignored_patterns: Path prefixes/names to ignore during snapshot generation.

    Returns:
        CanonicalSnapshot containing sorted entries and root SHA-256 digest.

    Raises:
        SnapshotSecurityError: If a symlink points outside the canonical workspace boundary.
    """
    root = Path(workspace_root).resolve()
    if not root.is_dir():
        raise SnapshotSecurityError(f"Workspace root '{root}' is not a directory")

    entries: list[SnapshotEntry] = []
    hasher = hashlib.sha256()

    all_files: list[Path] = []

    for current_dir, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [
            d for d in dirnames if d not in ignored_patterns and not d.startswith(".git")
        ]
        cur_path = Path(current_dir)

        # Check directory symlinks
        if cur_path.is_symlink():
            resolved = cur_path.resolve()
            if not (resolved == root or root in resolved.parents):
                raise SnapshotSecurityError(
                    f"Symlink directory '{cur_path}' escapes workspace boundary '{root}'"
                )

        for fname in sorted(filenames):
            if fname in ignored_patterns or fname.endswith(".pyc"):
                continue
            all_files.append(cur_path / fname)

    # Sort deterministically by relative POSIX path
    file_tuples = []
    for file_path in all_files:
        # Symlink boundary check
        if file_path.is_symlink():
            resolved = file_path.resolve()
            if not (resolved == root or root in resolved.parents):
                raise SnapshotSecurityError(
                    f"Symlink '{file_path}' points outside workspace root '{root}'"
                )
            if not resolved.is_file():
                continue

        try:
            rel = file_path.relative_to(root)
        except ValueError:
            raise SnapshotSecurityError(f"File '{file_path}' is outside root '{root}'")

        norm_rel = _normalize_relative_path(rel)
        file_tuples.append((norm_rel, file_path))

    file_tuples.sort(key=lambda x: x[0])

    for norm_rel, file_path in file_tuples:
        content = file_path.read_bytes()
        file_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"
        mode = file_path.stat().st_mode
        is_exec = bool(mode & 0o111)

        entry = SnapshotEntry(
            path=norm_rel,
            content_hash=file_hash,
            mode=mode,
            is_executable=is_exec,
        )
        entries.append(entry)

        # Update root aggregate hash
        manifest_line = f"{norm_rel}\0{file_hash}\0{1 if is_exec else 0}\n"
        hasher.update(manifest_line.encode("utf-8"))

    root_digest = f"sha256:{hasher.hexdigest()}"
    return CanonicalSnapshot(root_digest=root_digest, entries=entries)
