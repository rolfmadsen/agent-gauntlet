"""Tests for portable workspace snapshot generator, normalized relative paths, and hashing."""

import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.supervisor.core.snapshot import (
    generate_canonical_snapshot,
)


class TestPortableSnapshot(unittest.TestCase):
    """Verifies that snapshot generation produces deterministic, portable relative manifests."""

    def test_snapshot_uses_canonical_forward_slash_paths(self) -> None:
        """Paths in the canonical snapshot are relative and use '/' regardless of host OS."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
            (root / "README.md").write_text("# Project", encoding="utf-8")

            snapshot = generate_canonical_snapshot(root)
            self.assertEqual(len(snapshot.entries), 2)

            paths = [e.path for e in snapshot.entries]
            self.assertIn("README.md", paths)
            self.assertIn("src/main.py", paths)
            # Ensure no absolute paths leaked
            for p in paths:
                self.assertFalse(p.startswith("/"))
                self.assertFalse(":" in p)  # No Windows drive letters
                self.assertFalse("\\" in p)  # No backslashes

    def test_snapshot_hashes_bytes_deterministically(self) -> None:
        """Byte hashing is deterministic and captures file content digests."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "file.txt").write_bytes(b"deterministic content")

            snap1 = generate_canonical_snapshot(root)
            snap2 = generate_canonical_snapshot(root)

            self.assertEqual(snap1.root_digest, snap2.root_digest)
            self.assertTrue(snap1.root_digest.startswith("sha256:"))

    def test_snapshot_detects_symlink_escape_attempts(self) -> None:
        """Symlinks pointing outside the workspace are detected and rejected fail-closed."""
        with (
            tempfile.TemporaryDirectory() as tmp_dir,
            tempfile.TemporaryDirectory() as external_dir,
        ):
            root = Path(tmp_dir)
            ext = Path(external_dir)
            (ext / "secret.txt").write_text("secret", encoding="utf-8")

            # Create a symlink pointing outside
            symlink = root / "escape_link"
            symlink.symlink_to(ext / "secret.txt")

            with self.assertRaises(Exception):
                generate_canonical_snapshot(root)


if __name__ == "__main__":
    unittest.main()
