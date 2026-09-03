"""Black-box acceptance tests for features/scaffold (Safe Project Scaffolding)."""

import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.scaffold.models import ScaffoldStatus
from agent_gauntlet.features.scaffold.scaffolder import ProjectScaffolder


class TestProjectScaffolderAcceptance(unittest.TestCase):
    """Acceptance tests for ProjectScaffolder."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.scaffolder = ProjectScaffolder()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_scaffold_clean_workspace(self) -> None:
        """Scenario SC-01: Scaffolding an empty directory creates full project structure."""
        result = self.scaffolder.scaffold(self.workspace, stack="python", config_format="toml")

        self.assertTrue(result.success)
        self.assertGreater(len(result.entries), 5)

        # Core config & specifications
        self.assertTrue((self.workspace / "gauntlet.toml").is_file())
        self.assertTrue((self.workspace / "CONTEXT.md").is_file())
        self.assertTrue((self.workspace / "spec.md").is_file())
        self.assertTrue((self.workspace / "CLAUDE.md").is_file())
        self.assertTrue((self.workspace / "CODING_STANDARDS.md").is_file())

        # Tasks directory
        self.assertTrue((self.workspace / "tasks").is_dir())
        self.assertTrue((self.workspace / "tasks/001-bootstrap.md").is_file())

        # ADR directory
        self.assertTrue((self.workspace / "docs/adr").is_dir())
        self.assertTrue((self.workspace / "docs/adr/README.md").is_file())
        self.assertTrue((self.workspace / "docs/adr/0001-initial-architecture.md").is_file())

        # Agent guidelines & hooks
        self.assertTrue((self.workspace / ".agents/AGENTS.md").is_file())
        self.assertTrue((self.workspace / ".agents/hooks.json").is_file())

        # Plugin bundle and skills
        self.assertTrue((self.workspace / ".agents/plugins/agent-gauntlet/plugin.json").is_file())
        self.assertTrue((self.workspace / ".agents/plugins/agent-gauntlet/hooks.json").is_file())
        self.assertTrue(
            (self.workspace / ".agents/plugins/agent-gauntlet/skills/old-coder/SKILL.md").is_file()
        )
        self.assertTrue(
            (
                self.workspace
                / ".agents/plugins/agent-gauntlet/skills/old-coder/references/verifier.md"
            ).is_file()
        )
        self.assertTrue(
            (self.workspace / ".agents/plugins/agent-gauntlet/skills/grill-me/SKILL.md").is_file()
        )
        self.assertTrue(
            (
                self.workspace / ".agents/plugins/agent-gauntlet/skills/grill-with-docs/SKILL.md"
            ).is_file()
        )
        self.assertTrue(
            (self.workspace / ".agents/plugins/agent-gauntlet/skills/diagnose/SKILL.md").is_file()
        )
        self.assertTrue(
            (
                self.workspace / ".agents/plugins/agent-gauntlet/skills/code-review/SKILL.md"
            ).is_file()
        )

        # All entries should have CREATED status
        for entry in result.entries:
            self.assertEqual(entry.status, ScaffoldStatus.CREATED)

    def test_scaffold_idempotency_does_not_overwrite(self) -> None:
        """Scenario SC-02: Second run without --force skips all existing files."""
        self.scaffolder.scaffold(self.workspace, stack="python", config_format="toml")

        # Mutate a file
        context_file = self.workspace / "CONTEXT.md"
        custom_content = "# My Custom Domain Language\n\n- CustomTerm: Genus differentia."
        context_file.write_text(custom_content, encoding="utf-8")

        # Re-run scaffold without force
        second_result = self.scaffolder.scaffold(
            self.workspace, stack="python", config_format="toml", force=False
        )

        self.assertTrue(second_result.success)
        # Verify content was NOT overwritten
        self.assertEqual(context_file.read_text(encoding="utf-8"), custom_content)

        # Verify status is SKIPPED
        skipped_entries = [e for e in second_result.entries if e.status == ScaffoldStatus.SKIPPED]
        self.assertGreater(len(skipped_entries), 5)

    def test_scaffold_force_overwrites_existing(self) -> None:
        """Scenario SC-03: Running with force=True overwrites existing files."""
        self.scaffolder.scaffold(self.workspace, stack="python", config_format="toml")

        context_file = self.workspace / "CONTEXT.md"
        context_file.write_text("Old Modified Content", encoding="utf-8")

        force_result = self.scaffolder.scaffold(
            self.workspace, stack="python", config_format="toml", force=True
        )

        self.assertTrue(force_result.success)
        # Content should be restored to default template
        self.assertIn("Aristotle", context_file.read_text(encoding="utf-8"))

        overwritten_entries = [
            e for e in force_result.entries if e.status == ScaffoldStatus.OVERWRITTEN
        ]
        self.assertGreater(len(overwritten_entries), 0)

    def test_scaffold_creates_role_aware_agents_md(self) -> None:
        """Scenario SC-04: Scaffolding creates AGENTS.md with role-aware session handoff protocol, spec governance, and bundled skills."""
        self.scaffolder.scaffold(self.workspace, stack="python", config_format="toml")
        agents_md = (self.workspace / ".agents/AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("SESSION HANDOFF", agents_md)
        self.assertIn("Næste Rolle", agents_md)
        self.assertIn("code-review", agents_md)
        self.assertIn("Specification Governance", agents_md)
        self.assertIn("CODE REVIEW / AUDIT", agents_md)

    def test_scaffold_stack_specific_coding_standards(self) -> None:
        """Scenario SC-05: Scaffolder produces tailored CODING_STANDARDS.md per supported stack."""
        # 1. Python Stack
        self.scaffolder.scaffold(self.workspace, stack="python", config_format="toml", force=True)
        py_standards = (self.workspace / "CODING_STANDARDS.md").read_text(encoding="utf-8")
        self.assertIn("Google Python Style Guide", py_standards)
        self.assertIn("Type Annotations", py_standards)
        self.assertIn("Package-by-Feature", py_standards)
        self.assertIn("Google Docstrings", py_standards)
        self.assertIn("Args:", py_standards)
        self.assertIn("## 6. Concrete DO / DON'T Examples", py_standards)

        # 2. TypeScript Stack
        self.scaffolder.scaffold(
            self.workspace, stack="typescript", config_format="toml", force=True
        )
        ts_standards = (self.workspace / "CODING_STANDARDS.md").read_text(encoding="utf-8")
        self.assertIn("Google TypeScript Style Guide", ts_standards)
        self.assertIn("React", ts_standards)
        self.assertIn("Custom Hooks", ts_standards)
        self.assertIn("TSDoc Documentation Standard", ts_standards)
        self.assertIn("@param", ts_standards)
        self.assertIn("## 6. Concrete DO / DON'T Examples", ts_standards)

        # 3. Rust Stack
        self.scaffolder.scaffold(self.workspace, stack="rust", config_format="toml", force=True)
        rust_standards = (self.workspace / "CODING_STANDARDS.md").read_text(encoding="utf-8")
        self.assertIn("Official Rust API Guidelines", rust_standards)
        self.assertIn("Naming Conventions", rust_standards)
        self.assertIn("Error Handling", rust_standards)
        self.assertIn("Rustdoc Documentation Standard", rust_standards)
        self.assertIn("# Errors", rust_standards)
        self.assertIn("## 5. Concrete DO / DON'T Examples", rust_standards)

        # 4. Auto-detected TypeScript Stack
        (self.workspace / "tsconfig.json").write_text("{}", encoding="utf-8")
        self.scaffolder.scaffold(self.workspace, stack=None, config_format="toml", force=True)
        auto_ts_standards = (self.workspace / "CODING_STANDARDS.md").read_text(encoding="utf-8")
        self.assertIn("Google TypeScript Style Guide", auto_ts_standards)
        self.assertIn("TSDoc Documentation Standard", auto_ts_standards)

    def test_scaffold_typescript_solution_project_generates_tsc_b(self) -> None:
        """Scaffolding an existing solution tsconfig workspace must configure tsc -b."""
        (self.workspace / "tsconfig.json").write_text(
            '{\n  "files": [],\n  "references": [{ "path": "./tsconfig.app.json" }]\n}\n',
            encoding="utf-8",
        )
        result = self.scaffolder.scaffold(
            self.workspace, stack="typescript", config_format="toml", force=True
        )
        self.assertTrue(result.success)

        gauntlet_toml = (self.workspace / "gauntlet.toml").read_text(encoding="utf-8")
        self.assertIn('command = ["npx", "tsc", "-b"]', gauntlet_toml)

    def test_scaffold_polyglot_explicit_stacks_list(self) -> None:
        """Scenario SC-06: Scaffolding with multiple stacks produces composite CODING_STANDARDS.md."""
        result = self.scaffolder.scaffold(
            self.workspace, stacks=["typescript", "python"], config_format="toml", force=True
        )
        self.assertTrue(result.success)
        self.assertEqual(result.stacks, ["typescript", "python"])

        standards = (self.workspace / "CODING_STANDARDS.md").read_text(encoding="utf-8")
        self.assertIn("Polyglot", standards)
        self.assertIn("Transversal Engineering", standards)
        self.assertIn("TypeScript", standards)
        self.assertIn("Python", standards)
        self.assertIn("Cross-Stack Boundary", standards)
        self.assertIn("Google TypeScript Style Guide", standards)
        self.assertIn("Google Python Style Guide", standards)

    def test_scaffold_polyglot_explicit_comma_string(self) -> None:
        """Scenario SC-07: Comma-separated stack argument parses and builds composite standards."""
        result = self.scaffolder.scaffold(
            self.workspace, stack="typescript,rust", config_format="toml", force=True
        )
        self.assertTrue(result.success)
        self.assertEqual(result.stacks, ["typescript", "rust"])

        standards = (self.workspace / "CODING_STANDARDS.md").read_text(encoding="utf-8")
        self.assertIn("Polyglot", standards)
        self.assertIn("TypeScript", standards)
        self.assertIn("Rust", standards)
        self.assertIn("Official Rust API Guidelines", standards)

    def test_scaffold_polyglot_auto_detection(self) -> None:
        """Scenario SC-08: Auto-detecting multiple stacks in subdirectories generates composite standards."""
        (self.workspace / "frontend").mkdir()
        (self.workspace / "frontend/tsconfig.json").touch()
        (self.workspace / "backend").mkdir()
        (self.workspace / "backend/pyproject.toml").touch()

        result = self.scaffolder.scaffold(
            self.workspace, stack=None, config_format="toml", force=True
        )
        self.assertTrue(result.success)
        self.assertIn("typescript", result.stacks)
        self.assertIn("python", result.stacks)

        standards = (self.workspace / "CODING_STANDARDS.md").read_text(encoding="utf-8")
        self.assertIn("Polyglot", standards)
        self.assertIn("TypeScript", standards)
        self.assertIn("Python", standards)

    def test_scaffold_skips_bootstrap_task_when_existing_tasks_present(self) -> None:
        """Scenario SC-09: Scaffolding a workspace with existing tasks does NOT create 001-bootstrap.md."""
        tasks_dir = self.workspace / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        (tasks_dir / "043-wasm-engine.md").write_text("# Task 043", encoding="utf-8")

        result = self.scaffolder.scaffold(self.workspace, stack="python")
        self.assertTrue(result.success)

        # 001-bootstrap.md must NOT exist
        self.assertFalse((tasks_dir / "001-bootstrap.md").exists())
        # The entry in result.entries must be marked as SKIPPED
        bootstrap_entries = [e for e in result.entries if "001-bootstrap.md" in e.path]
        self.assertEqual(len(bootstrap_entries), 1)
        self.assertEqual(bootstrap_entries[0].status, ScaffoldStatus.SKIPPED)

    def test_scaffold_skips_initial_adr_when_existing_adrs_present(self) -> None:
        """Scenario SC-10: Scaffolding a workspace with existing ADRs does NOT create 0001-initial-architecture.md."""
        adr_dir = self.workspace / "docs/adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "0003-surgical-gatekeeper.md").write_text("# ADR 0003", encoding="utf-8")

        result = self.scaffolder.scaffold(self.workspace, stack="python")
        self.assertTrue(result.success)

        # 0001-initial-architecture.md must NOT exist
        self.assertFalse((adr_dir / "0001-initial-architecture.md").exists())
        # The entry in result.entries must be marked as SKIPPED
        adr_entries = [e for e in result.entries if "0001-initial-architecture.md" in e.path]
        self.assertEqual(len(adr_entries), 1)
        self.assertEqual(adr_entries[0].status, ScaffoldStatus.SKIPPED)


if __name__ == "__main__":
    unittest.main()
