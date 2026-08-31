"""Tests for stack detection and default profile generation."""

import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.stacks.detector import (
    detect_stack,
    detect_stacks,
    get_typescript_typecheck_command,
    has_typescript_project_references,
)
from agent_gauntlet.features.stacks.profiles import (
    SUPPORTED_STACKS,
    get_default_stack_profile,
    get_typescript_default_layers,
)


class TestStackDetector(unittest.TestCase):
    """Tests for auto-detecting project stacks from filesystem markers."""

    def test_detect_python_from_pyproject(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "pyproject.toml").touch()
            self.assertEqual(detect_stack(tmpdir), "python")
            self.assertEqual(detect_stacks(tmpdir), ["python"])

    def test_detect_python_from_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "requirements.txt").touch()
            self.assertEqual(detect_stack(tmpdir), "python")
            self.assertEqual(detect_stacks(tmpdir), ["python"])

    def test_detect_typescript_from_tsconfig(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "tsconfig.json").touch()
            self.assertEqual(detect_stack(tmpdir), "typescript")
            self.assertEqual(detect_stacks(tmpdir), ["typescript"])

    def test_detect_typescript_from_package_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "package.json").touch()
            self.assertEqual(detect_stack(tmpdir), "typescript")
            self.assertEqual(detect_stacks(tmpdir), ["typescript"])

    def test_detect_rust_from_cargo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "Cargo.toml").touch()
            self.assertEqual(detect_stack(tmpdir), "rust")
            self.assertEqual(detect_stacks(tmpdir), ["rust"])

    def test_detect_unknown_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertIsNone(detect_stack(tmpdir))
            self.assertEqual(detect_stacks(tmpdir), [])

    def test_detect_polyglot_subdirectories(self) -> None:
        """Scenario: monorepo with frontend/ and backend/."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "frontend").mkdir()
            (ws / "frontend/package.json").touch()
            (ws / "backend").mkdir()
            (ws / "backend/pyproject.toml").touch()

            detected = detect_stacks(ws)
            self.assertIn("typescript", detected)
            self.assertIn("python", detected)
            self.assertEqual(len(detected), 2)

    def test_detect_polyglot_three_stacks(self) -> None:
        """Scenario: repo with crates/ (rust), web/ (ts), and scripts/ (python)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "crates/engine").mkdir(parents=True)
            (ws / "crates/engine/Cargo.toml").touch()
            (ws / "web").mkdir()
            (ws / "web/tsconfig.json").touch()
            (ws / "services/api").mkdir(parents=True)
            (ws / "services/api/requirements.txt").touch()

            detected = detect_stacks(ws)
            self.assertIn("rust", detected)
            self.assertIn("typescript", detected)
            self.assertIn("python", detected)
            self.assertEqual(len(detected), 3)


class TestTypeScriptProjectReferencesDetector(unittest.TestCase):
    """Tests for smart TypeScript project references / solution style detection."""

    def test_single_tsconfig_has_no_project_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "tsconfig.json").write_text(
                '{\n  "compilerOptions": {\n    "strict": true\n  },\n  "include": ["src"]\n}\n',
                encoding="utf-8",
            )
            self.assertFalse(has_typescript_project_references(ws))
            self.assertEqual(get_typescript_typecheck_command(ws), ["npx", "tsc", "--noEmit"])

    def test_solution_tsconfig_with_references_array(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "tsconfig.json").write_text(
                '{\n  "files": [],\n  "references": [\n    { "path": "./tsconfig.app.json" },\n    { "path": "./tsconfig.node.json" }\n  ]\n}\n',
                encoding="utf-8",
            )
            self.assertTrue(has_typescript_project_references(ws))
            self.assertEqual(get_typescript_typecheck_command(ws), ["npx", "tsc", "-b"])

    def test_solution_tsconfig_with_jsonc_comments_and_trailing_commas(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "tsconfig.json").write_text(
                """// Solution tsconfig with comments
{
  /* Root files array is empty */
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" }, // main app
    { "path": "./tsconfig.node.json" },
  ],
}
""",
                encoding="utf-8",
            )
            self.assertTrue(has_typescript_project_references(ws))
            self.assertEqual(get_typescript_typecheck_command(ws), ["npx", "tsc", "-b"])

    def test_tsconfig_app_json_with_root_tsconfig_without_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "tsconfig.json").write_text(
                '{\n  "compilerOptions": {\n    "strict": true\n  }\n}\n',
                encoding="utf-8",
            )
            (ws / "tsconfig.app.json").write_text(
                '{\n  "compilerOptions": {\n    "strict": true\n  }\n}\n',
                encoding="utf-8",
            )
            self.assertTrue(has_typescript_project_references(ws))
            self.assertEqual(
                get_typescript_typecheck_command(ws),
                ["npx", "tsc", "--noEmit", "-p", "tsconfig.app.json"],
            )

    def test_tsconfig_app_json_standalone_without_root_tsconfig(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "tsconfig.app.json").write_text(
                '{\n  "compilerOptions": {\n    "strict": true\n  }\n}\n',
                encoding="utf-8",
            )
            self.assertTrue(has_typescript_project_references(ws))
            self.assertEqual(
                get_typescript_typecheck_command(ws),
                ["npx", "tsc", "--noEmit", "-p", "tsconfig.app.json"],
            )

    def test_default_typecheck_command_when_no_workspace_provided(self) -> None:
        self.assertEqual(get_typescript_typecheck_command(None), ["npx", "tsc", "--noEmit"])


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
        types_layer = next(l for l in layers if l.name == "types")
        self.assertEqual(types_layer.command, ["npx", "tsc", "--noEmit"])

    def test_typescript_default_profile_with_solution_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "tsconfig.json").write_text(
                '{"files": [], "references": [{"path": "./tsconfig.app.json"}]}',
                encoding="utf-8",
            )
            layers = get_typescript_default_layers(workspace_path=ws)
            types_layer = next(l for l in layers if l.name == "types")
            self.assertEqual(types_layer.command, ["npx", "tsc", "-b"])

            profile_layers = get_default_stack_profile("typescript", workspace_path=ws)
            p_types_layer = next(l for l in profile_layers if l.name == "types")
            self.assertEqual(p_types_layer.command, ["npx", "tsc", "-b"])

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

