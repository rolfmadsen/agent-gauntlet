"""Tests for agent-gauntlet template completeness and distribution tree."""

import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.scaffold.scaffolder import ProjectScaffolder

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestTemplateCompleteness(unittest.TestCase):
    """Verifies that templates/plugin and packaged templates are 100% complete with all references."""

    def test_canonical_template_tree_structure(self) -> None:
        """The canonical templates/plugin and src templates must contain all required files."""
        candidates = [
            REPO_ROOT / "templates" / "plugin" / "agent-gauntlet",
            REPO_ROOT / "src" / "agent_gauntlet" / "templates" / "plugin" / "agent-gauntlet",
            REPO_ROOT / "plugins" / "agent-gauntlet",
        ]
        template_dir = next((d for d in candidates if d.is_dir()), None)
        self.assertIsNotNone(template_dir, f"No template directory found in {candidates}")
        assert template_dir is not None

        # Verify plugin manifest and hooks
        self.assertTrue((template_dir / "plugin.json").is_file(), "Missing plugin.json")
        self.assertTrue((template_dir / "hooks.json").is_file(), "Missing hooks.json")

        # Verify old-coder and all 4 references
        old_coder = template_dir / "skills" / "old-coder"
        self.assertTrue((old_coder / "SKILL.md").is_file(), "Missing old-coder/SKILL.md")
        refs_dir = old_coder / "references"
        self.assertTrue(refs_dir.is_dir(), "Missing old-coder/references directory")
        for ref_file in ["verifier.md", "templates.md", "gauntlet.md", "verifier-case-study.md"]:
            rf = refs_dir / ref_file
            self.assertTrue(rf.is_file(), f"Missing old-coder/references/{ref_file}")
            self.assertGreater(rf.stat().st_size, 200, f"{ref_file} must not be an empty stub")

        # Verify diagnose skill and scripts
        diagnose = template_dir / "skills" / "diagnose"
        self.assertTrue((diagnose / "SKILL.md").is_file(), "Missing diagnose/SKILL.md")
        self.assertTrue(
            (diagnose / "scripts" / "hitl-loop.template.sh").is_file(),
            "Missing hitl-loop.template.sh",
        )

        # Verify grill-with-docs and format references
        gwd = template_dir / "skills" / "grill-with-docs"
        self.assertTrue((gwd / "SKILL.md").is_file(), "Missing grill-with-docs/SKILL.md")
        self.assertTrue((gwd / "ADR-FORMAT.md").is_file(), "Missing ADR-FORMAT.md")
        self.assertTrue((gwd / "CONTEXT-FORMAT.md").is_file(), "Missing CONTEXT-FORMAT.md")

    def test_scaffolder_copies_complete_plugin_tree_recursively(self) -> None:
        """ProjectScaffolder.scaffold must copy the complete plugin tree with all references."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = Path(tmp_dir)
            result = ProjectScaffolder().scaffold(workspace=ws, stack="python")
            self.assertTrue(result.success)

            # 1. Verify plugin copied recursively under .agents/plugins/agent-gauntlet/
            plugin_dir = ws / ".agents" / "plugins" / "agent-gauntlet"
            self.assertTrue(plugin_dir.is_dir(), "Plugin directory was not created")
            self.assertTrue((plugin_dir / "plugin.json").is_file(), "Missing plugin.json in target")
            self.assertTrue((plugin_dir / "hooks.json").is_file(), "Missing hooks.json in target")

            # Verify old-coder references in target
            verifier_ref = plugin_dir / "skills" / "old-coder" / "references" / "verifier.md"
            self.assertTrue(
                verifier_ref.is_file(),
                "verifier.md reference was not copied to target plugin directory",
            )
            self.assertGreater(verifier_ref.stat().st_size, 200)

            templates_ref = plugin_dir / "skills" / "old-coder" / "references" / "templates.md"
            self.assertTrue(templates_ref.is_file())

            # Verify diagnose script in target
            hitl_script = plugin_dir / "skills" / "diagnose" / "scripts" / "hitl-loop.template.sh"
            self.assertTrue(hitl_script.is_file())

            # 2. Verify tasks/001-bootstrap.md exists and NO root task.md or .agents/task.md
            self.assertTrue((ws / "tasks" / "001-bootstrap.md").is_file())
            self.assertFalse((ws / "task.md").exists(), "Must NOT create root task.md")
            self.assertFalse(
                (ws / ".agents" / "task.md").exists(), "Must NOT create .agents/task.md"
            )

            # 3. Verify gauntlet.toml contains path manifest
            cfg_text = (ws / "gauntlet.toml").read_text(encoding="utf-8")
            self.assertIn('tasks_dir = "tasks"', cfg_text)
            self.assertIn('spec_file = "spec.md"', cfg_text)


if __name__ == "__main__":
    unittest.main()
