"""Tests for platform seams, dependency direction, and unsupported platform fail-fast."""

import ast
import inspect
import unittest

from agent_gauntlet.features.supervisor.core import seams


class TestPlatformSeams(unittest.TestCase):
    """Verifies that platform seams remain pure interfaces with no leaked OS dependencies."""

    def test_core_seams_do_not_import_os_specific_modules(self) -> None:
        """Portable core seams must not import OS-specific modules or process runners."""
        source = inspect.getsource(seams)
        tree = ast.parse(source)

        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module)

        forbidden = {"systemd", "subprocess", "posix", "nt", "ctypes", "winreg"}
        for mod in imported_modules:
            root_mod = mod.split(".")[0]
            self.assertNotIn(
                root_mod,
                forbidden,
                f"Portable core seams must not import forbidden OS module: {mod}",
            )

    def test_unsupported_platform_fails_fast(self) -> None:
        """Attempting to resolve an unsupported platform raises UnsupportedPlatformError."""
        with self.assertRaises(seams.UnsupportedPlatformError):
            seams.get_platform_seam("unsupported_os_xyz")


if __name__ == "__main__":
    unittest.main()
