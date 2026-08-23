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

        # Skills
        self.assertTrue((self.workspace / ".agents/skills/old-coder/SKILL.md").is_file())
        self.assertTrue((self.workspace / ".agents/skills/grill-me/SKILL.md").is_file())
        self.assertTrue((self.workspace / ".agents/skills/grill-with-docs/SKILL.md").is_file())
        self.assertTrue((self.workspace / ".agents/skills/diagnose/SKILL.md").is_file())

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
        second_result = self.scaffolder.scaffold(self.workspace, stack="python", config_format="toml", force=False)

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

        force_result = self.scaffolder.scaffold(self.workspace, stack="python", config_format="toml", force=True)

        self.assertTrue(force_result.success)
        # Content should be restored to default template
        self.assertIn("Aristotle", context_file.read_text(encoding="utf-8"))

        overwritten_entries = [e for e in force_result.entries if e.status == ScaffoldStatus.OVERWRITTEN]
        self.assertGreater(len(overwritten_entries), 0)


if __name__ == "__main__":
    unittest.main()
