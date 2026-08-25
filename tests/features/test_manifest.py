"""Acceptance and property tests for CanonicalWorkspaceManifest and workspace-escape protection."""

import os
import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.evidence.source_state import (
    WorkspaceEscapeError,
    compute_workspace_manifest,
)


class TestCanonicalWorkspaceManifest(unittest.TestCase):
    """Tests for CanonicalWorkspaceManifest deterministic hashing and safety invariants."""

    def test_manifest_deterministic_across_identical_runs(self) -> None:
        """Invariant: Computing manifest on unchanged directory yields identical digest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
            (root / "README.md").write_text("# Test Project", encoding="utf-8")

            m1 = compute_workspace_manifest(root)
            m2 = compute_workspace_manifest(root)

            self.assertEqual(m1.source_manifest_digest, m2.source_manifest_digest)
            self.assertEqual(m1.source_content_digest, m2.source_content_digest)
            self.assertEqual(m1.included_files_count, 2)
            self.assertEqual(m1.files, ["README.md", "src/main.py"])

    def test_manifest_detects_content_change(self) -> None:
        """Invariant: Content change flips source content and manifest digests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            file_p = root / "src" / "main.py"
            file_p.write_text("print('version 1')", encoding="utf-8")
            m1 = compute_workspace_manifest(root)

            file_p.write_text("print('version 2')", encoding="utf-8")
            m2 = compute_workspace_manifest(root)

            self.assertNotEqual(m1.source_manifest_digest, m2.source_manifest_digest)
            self.assertNotEqual(m1.source_content_digest, m2.source_content_digest)

    def test_manifest_detects_chmod_executable_change(self) -> None:
        """Invariant: POSIX chmod +x changes source_manifest_digest while preserving source_content_digest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "tools").mkdir()
            script = root / "tools" / "run.sh"
            script.write_text("#!/bin/sh\necho hi", encoding="utf-8")
            os.chmod(script, 0o644)

            m1 = compute_workspace_manifest(root)

            os.chmod(script, 0o755)
            m2 = compute_workspace_manifest(root)

            self.assertNotEqual(
                m1.source_manifest_digest,
                m2.source_manifest_digest,
                "Executable mode change must alter source_manifest_digest",
            )
            self.assertEqual(
                m1.source_content_digest,
                m2.source_content_digest,
                "Content digest must remain portable across permission changes",
            )

    def test_symlink_workspace_escape_fails_closed(self) -> None:
        """Invariant: Symlink resolving outside workspace root raises WorkspaceEscapeError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "workspace"
            root.mkdir()
            outside_file = Path(tmpdir) / "secret.txt"
            outside_file.write_text("super secret", encoding="utf-8")

            (root / "src").mkdir()
            symlink = root / "src" / "leak.txt"
            symlink.symlink_to(outside_file)

            with self.assertRaises(WorkspaceEscapeError):
                compute_workspace_manifest(root)

    def test_symlink_inside_workspace_is_digested_safely(self) -> None:
        """Invariant: Symlink pointing inside workspace is safely digested without escape error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            target = root / "src" / "target.py"
            target.write_text("print('target')", encoding="utf-8")

            link = root / "src" / "alias.py"
            link.symlink_to(target)

            manifest = compute_workspace_manifest(root)
            self.assertIn("src/alias.py", manifest.files)
            self.assertIn("src/target.py", manifest.files)
            self.assertEqual(manifest.included_files_count, 2)

    def test_cache_directories_and_evidence_files_excluded(self) -> None:
        """Invariant: Cache folders and evidence output files are excluded from source manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("pass", encoding="utf-8")
            (root / "src" / "__pycache__").mkdir()
            (root / "src" / "__pycache__" / "app.cpython-312.pyc").write_bytes(b"cached")
            (root / ".venv").mkdir()
            (root / ".venv" / "lib.py").write_text("pass", encoding="utf-8")
            (root / "verification-report.json").write_text("{}", encoding="utf-8")
            (root / "evidence.json").write_text("{}", encoding="utf-8")
            (root / "evidence.md").write_text("# Evidence", encoding="utf-8")

            manifest = compute_workspace_manifest(root)
            self.assertEqual(manifest.files, ["src/app.py"])
            self.assertEqual(manifest.included_files_count, 1)

    def test_umask_variation_preserves_digest(self) -> None:
        """Invariant: Non-executable permission differences (e.g. 644 vs 664) yield identical manifest digest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            f = root / "src" / "app.py"
            f.write_text("print('hello')", encoding="utf-8")
            os.chmod(f, 0o644)
            m1 = compute_workspace_manifest(root)

            os.chmod(f, 0o664)
            m2 = compute_workspace_manifest(root)
            self.assertEqual(m1.source_manifest_digest, m2.source_manifest_digest)

    def test_policy_digest_tracks_hooks_and_workflows(self) -> None:
        """Invariant: Modifications to .agents/hooks.json or .github/workflows alter policy_digest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".agents").mkdir()
            hooks = root / ".agents" / "hooks.json"
            hooks.write_text("{}", encoding="utf-8")
            m1 = compute_workspace_manifest(root)

            hooks.write_text('{"hooks": []}', encoding="utf-8")
            m2 = compute_workspace_manifest(root)
            self.assertNotEqual(m1.policy_digest, m2.policy_digest)


if __name__ == "__main__":
    unittest.main()
