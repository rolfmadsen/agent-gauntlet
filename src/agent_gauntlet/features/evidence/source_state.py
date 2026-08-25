"""Deterministic, fail-closed canonical workspace manifest and state binding."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from agent_gauntlet.features.evidence.models import VcsMetadata

DEFAULT_SCOPES = (
    "src",
    "tests",
    "tools",
    "plugins",
    "spec.md",
    "README.md",
    "pyproject.toml",
)

EXCLUDED_DIRS = {
    ".git",
    ".hypothesis",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".vscode",
    "__pycache__",
}

EXCLUDED_FILES = {
    ".DS_Store",
    ".coverage",
    "attestation.bundle",
    "coverage.xml",
    "evidence.json",
    "evidence.md",
    "verification-report.json",
}

NO_GIT = "(no git)"


class WorkspaceEscapeError(Exception):
    """Raised when a symlink or path traversal resolves outside the canonical workspace root."""


class UnicodePathError(Exception):
    """Raised when a workspace file path contains invalid or non-UTF-8 characters."""


@dataclass(frozen=True)
class CanonicalWorkspaceManifest:
    """Canonical representation of workspace source files, modes, and digests."""

    files: list[str] = field(default_factory=list)
    included_files_count: int = 0
    source_content_digest: str = ""
    source_manifest_digest: str = ""
    config_digest: str = ""
    task_digest: str = ""
    policy_digest: str = ""
    vcs: VcsMetadata | None = None


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _is_excluded(rel_path: Path) -> bool:
    """Check if relative path matches exclusion rules."""
    parts = rel_path.parts
    if any(part in EXCLUDED_DIRS or part.endswith(".egg-info") for part in parts):
        return True
    if rel_path.name in EXCLUDED_FILES or rel_path.suffix == ".pyc":
        return True
    return False


def _hash_file_content(path: Path) -> str:
    try:
        data = path.read_bytes()
        return hashlib.sha256(data).hexdigest()
    except OSError as err:
        raise RuntimeError(f"Cannot read source file '{path}': {err}") from err


def _get_file_mode(path: Path, is_symlink: bool) -> str:
    if is_symlink:
        return "120000"
    try:
        st_mode = path.stat().st_mode
        mode_octal = st_mode & 0o777
        # On POSIX, use actual mode; if non-POSIX fallback, standard permissions
        if os.name != "nt":
            return f"{mode_octal:03o}"
        # Portable Windows fallback
        is_exec = (st_mode & 0o111) != 0 or path.suffix.lower() in (".sh", ".py", ".bat", ".cmd", ".exe")
        return "755" if is_exec else "644"
    except OSError:
        return "644"


def _compute_digest_of_files(root: Path, files: Sequence[Path]) -> str:
    """Compute a single digest over a sequence of files."""
    digest = hashlib.sha256()
    for f in sorted(files):
        if f.is_file() and not _is_excluded(f.relative_to(root)):
            try:
                rel = f.relative_to(root).as_posix().encode("utf-8")
                content = f.read_bytes()
                digest.update(len(rel).to_bytes(8, "big"))
                digest.update(rel)
                digest.update(len(content).to_bytes(8, "big"))
                digest.update(content)
            except OSError:
                continue
    return digest.hexdigest()


def compute_workspace_manifest(
    root: Path | None = None,
    scopes: Sequence[str] | None = None,
) -> CanonicalWorkspaceManifest:
    """
    Computes a deterministic, platform-independent canonical workspace manifest.
    Detects symlink workspace escapes and tracks content and POSIX mode digests.
    """
    target_root = (root or Path.cwd()).resolve()
    target_scopes = tuple(scopes) if scopes else DEFAULT_SCOPES

    items: list[tuple[str, str, str]] = []  # (normalized_rel_path, content_hash, mode_str)

    for scope in target_scopes:
        candidate = target_root / scope
        if not candidate.exists() and not candidate.is_symlink():
            continue

        file_paths = [candidate] if (candidate.is_file() or candidate.is_symlink()) else list(candidate.rglob("*"))

        for path in file_paths:
            if not path.is_file() and not path.is_symlink():
                continue

            try:
                rel_path = path.relative_to(target_root)
                rel_str = rel_path.as_posix()
            except ValueError:
                continue

            # Validate UTF-8 and normalize
            try:
                normalized_rel = unicodedata.normalize("NFC", rel_str)
            except Exception as err:
                raise UnicodePathError(f"Path contains invalid characters: '{rel_str}'") from err

            if _is_excluded(rel_path):
                continue

            if path.is_symlink():
                target_str = os.readlink(path)
                resolved = path.resolve()
                try:
                    # Check workspace escape: resolved target must be within target_root
                    resolved.relative_to(target_root)
                except ValueError as err:
                    raise WorkspaceEscapeError(
                        f"Symlink '{rel_str}' resolves outside workspace root: target='{target_str}', resolved='{resolved}'"
                    ) from err

                content_hash = hashlib.sha256(target_str.encode("utf-8")).hexdigest()
                mode_str = _get_file_mode(path, is_symlink=True)
            else:
                content_hash = _hash_file_content(path)
                mode_str = _get_file_mode(path, is_symlink=False)

            items.append((normalized_rel, content_hash, mode_str))

    # Sort lexicographically by relative path bytes
    sorted_items = sorted(items, key=lambda x: x[0].encode("utf-8"))
    file_list = [item[0] for item in sorted_items]

    # Generate canonical manifest lines (<hash> <mode> <path>\n)
    manifest_lines = "".join(f"{h} {m} {p}\n" for p, h, m in sorted_items)
    source_manifest_digest = hashlib.sha256(manifest_lines.encode("utf-8")).hexdigest()

    # Generate portable content lines (<hash> <path>\n)
    content_lines = "".join(f"{h} {p}\n" for p, h, _ in sorted_items)
    source_content_digest = hashlib.sha256(content_lines.encode("utf-8")).hexdigest()

    # Auxiliary digests
    config_files = [target_root / "gauntlet.toml", target_root / "gauntlet.json"]
    config_digest = _compute_digest_of_files(target_root, config_files)

    task_dir = target_root / "tasks"
    task_files = list(task_dir.glob("*.md")) if task_dir.is_dir() else []
    task_digest = _compute_digest_of_files(target_root, task_files)

    policy_files = [target_root / "spec.md", target_root / "CONTEXT.md"]
    adr_dir = target_root / "docs" / "adr"
    if adr_dir.is_dir():
        policy_files.extend(adr_dir.glob("*.md"))
    policy_digest = _compute_digest_of_files(target_root, policy_files)

    # Git metadata probe
    vcs_obj: VcsMetadata | None = None
    git_dir = target_root / ".git"
    if git_dir.exists():
        head_res = _git(target_root, "rev-parse", "--short", "HEAD", check=False)
        if head_res.returncode == 0:
            head = os.fsdecode(head_res.stdout).strip()
            commit_res = _git(target_root, "log", "-1", "--format=%h", "--", *target_scopes, check=False)
            commit = os.fsdecode(commit_res.stdout).strip() if commit_res.returncode == 0 else head
            status_res = _git(target_root, "status", "--porcelain", check=False)
            is_dirty = bool(status_res.stdout.strip())
            vcs_obj = VcsMetadata(type="git", head=head, commit=commit, is_dirty=is_dirty)

    return CanonicalWorkspaceManifest(
        files=file_list,
        included_files_count=len(file_list),
        source_content_digest=source_content_digest,
        source_manifest_digest=source_manifest_digest,
        config_digest=config_digest,
        task_digest=task_digest,
        policy_digest=policy_digest,
        vcs=vcs_obj,
    )


def compute_source_state(root: Path | None = None) -> tuple[str, str, str]:
    """
    Backward-compatible entry point returning (head, commit, tree_digest).
    """
    target_root = (root or Path.cwd()).resolve()
    manifest = compute_workspace_manifest(target_root)

    head = manifest.vcs.head if manifest.vcs else NO_GIT
    commit = manifest.vcs.commit if manifest.vcs else NO_GIT
    tree_digest = manifest.source_manifest_digest[:16]

    return head, commit, tree_digest


def main(root: Path | None = None) -> int:
    target_root = (root or Path.cwd()).resolve()
    try:
        manifest = compute_workspace_manifest(target_root)
    except Exception as error:
        print(f"source-state error: {error}", file=sys.stderr)
        return 2

    head = manifest.vcs.head if manifest.vcs else NO_GIT
    commit = manifest.vcs.commit if manifest.vcs else NO_GIT
    print(f"head:            {head}")
    print(f"source commit:   {commit}")
    print(f"manifest digest: {manifest.source_manifest_digest[:16]}")
    print(f"content digest:  {manifest.source_content_digest[:16]}")
    print(f"files count:     {manifest.included_files_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
