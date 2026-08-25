"""Tests for stack detection and default profile generation."""

import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.stacks.detector import detect_stack
from agent_gauntlet.features.stacks.profiles import (
    SUPPORTED_STACKS,
    get_default_stack_profile,
)


class TestStackDetector(unittest.TestCase):
    """Tests for auto-detecting project stacks from filesystem markers."""

    def test_detect_python_from_pyproject(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "pyproject.toml").touch()
            self.assertEqual(detect_stack(tmpdir), "python")

    def test_detect_python_from_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "requirements.txt").touch()
            self.assertEqual(detect_stack(tmpdir), "python")

    def test_detect_typescript_from_tsconfig(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "tsconfig.json").touch()
            self.assertEqual(detect_stack(tmpdir), "typescript")

    def test_detect_typescript_from_package_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "package.json").touch()
            self.assertEqual(detect_stack(tmpdir), "typescript")

    def test_detect_rust_from_cargo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "Cargo.toml").touch()
            self.assertEqual(detect_stack(tmpdir), "rust")

    def test_detect_unknown_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertIsNone(detect_stack(tmpdir))


class TestStackProfiles(unittest.TestCase):
    """Tests for default stack verification layer profiles."""

    def test_supported_stacks_contains_tier1(self) -> None:
        self.assertIn("python", SUPPORTED_STACKS)
        self.assertIn("typescript", SUPPORTED_STACKS)
        self.assertIn("rust", SUPPORTED_STACKS)

    def test_python_default_profile(self) -> None:
        layers = get_default_stack_profile("python")
        names = [layer.name for layer in layers]
        self.assertIn("lint", names)
        self.assertIn("types", names)
        self.assertIn("unit", names)

    def test_typescript_default_profile(self) -> None:
        layers = get_default_stack_profile("typescript")
        names = [layer.name for layer in layers]
        self.assertIn("lint", names)
        self.assertIn("types", names)
        self.assertIn("unit", names)

    def test_rust_default_profile(self) -> None:
        layers = get_default_stack_profile("rust")
        names = [layer.name for layer in layers]
        self.assertIn("lint", names)
        self.assertIn("types", names)
        self.assertIn("unit", names)

    def test_unsupported_stack_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            get_default_stack_profile("unsupported_stack_xyz")


if __name__ == "__main__":
    unittest.main()
