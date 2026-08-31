"""Tests for agent-gauntlet doctor workspace integrity and orphan/duplicate diagnostics."""

import json
import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.doctor.checker import DoctorChecker
from agent_gauntlet.features.doctor.models import FindingSeverity
from agent_gauntlet.features.scaffold.scaffolder import ProjectScaffolder


class TestDoctorDiagnostics(unittest.TestCase):
    """Tests for agent-gauntlet doctor checker and migration prompt generator."""

    def test_doctor_on_healthy_scaffolded_workspace(self) -> None:
        """A freshly initialized workspace must report healthy with no critical errors."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = Path(tmp_dir)
            ProjectScaffolder().scaffold(workspace=ws, stack="python")

            checker = DoctorChecker()
            report = checker.check_workspace(ws)

            self.assertTrue(report.healthy)
            self.assertFalse(report.has_errors)
            error_findings = [f for f in report.findings if f.severity == FindingSeverity.ERROR]
            self.assertEqual(len(error_findings), 0)

    def test_doctor_detects_missing_skill_references(self) -> None:
        """Doctor must flag missing old-coder references as critical error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = Path(tmp_dir)
            ProjectScaffolder().scaffold(workspace=ws, stack="python")

            # Intentionally remove verifier.md reference
            verifier_file = (
                ws
                / ".agents"
                / "plugins"
                / "agent-gauntlet"
                / "skills"
                / "old-coder"
                / "references"
                / "verifier.md"
            )
            if verifier_file.is_file():
                verifier_file.unlink()

            checker = DoctorChecker()
            report = checker.check_workspace(ws)

            self.assertFalse(report.healthy)
            self.assertTrue(report.has_errors)
            ref_findings = [
                f for f in report.findings if "verifier.md" in f.path or "verifier.md" in f.message
            ]
            self.assertGreater(len(ref_findings), 0)
            self.assertEqual(ref_findings[0].severity, FindingSeverity.ERROR)
            self.assertIn("references/verifier.md", report.migration_prompt)

    def test_doctor_detects_stray_root_task_and_shadow_specs(self) -> None:
        """Doctor must flag root task.md and shadow .agents/spec.md."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = Path(tmp_dir)
            ProjectScaffolder().scaffold(workspace=ws, stack="python")

            # Create rogue task.md and shadow spec.md
            (ws / "task.md").write_text("# Rogue Task", encoding="utf-8")
            (ws / ".agents" / "spec.md").write_text("# Shadow Spec", encoding="utf-8")

            checker = DoctorChecker()
            report = checker.check_workspace(ws)

            self.assertFalse(report.healthy)
            task_findings = [f for f in report.findings if f.path == "task.md"]
            self.assertGreater(len(task_findings), 0)
            self.assertEqual(task_findings[0].severity, FindingSeverity.ERROR)

            spec_findings = [f for f in report.findings if ".agents/spec.md" in f.path]
            self.assertGreater(len(spec_findings), 0)

            # Migration prompt must instruct moving task.md to tasks/
            self.assertIn("task.md", report.migration_prompt)
            self.assertIn("tasks/", report.migration_prompt)

    def test_doctor_detects_duplicate_skills_in_dot_agents(self) -> None:
        """Doctor must warn if .agents/skills has duplicate skills already provided by the plugin."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = Path(tmp_dir)
            ProjectScaffolder().scaffold(workspace=ws, stack="python")

            # Create loose duplicate skill in .agents/skills/old-coder
            duplicate_dir = ws / ".agents" / "skills" / "old-coder"
            duplicate_dir.mkdir(parents=True, exist_ok=True)
            (duplicate_dir / "SKILL.md").write_text("# Old Coder Duplicate", encoding="utf-8")

            checker = DoctorChecker()
            report = checker.check_workspace(ws)

            dup_findings = [
                f
                for f in report.findings
                if "duplicate" in f.message.lower() or "redundant" in f.message.lower()
            ]
            self.assertGreater(len(dup_findings), 0)

    def test_doctor_detects_solution_tsconfig_with_blind_tsc_noemit(self) -> None:
        """Doctor must warn if TypeScript project has project references but gauntlet runs blind tsc --noEmit."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = Path(tmp_dir)
            ProjectScaffolder().scaffold(workspace=ws, stack="typescript")

            # Simulate a solution-style tsconfig with references
            (ws / "tsconfig.json").write_text(
                '{\n  "files": [],\n  "references": [\n    { "path": "./tsconfig.app.json" }\n  ]\n}\n',
                encoding="utf-8",
            )
            # Simulate a gauntlet.toml with blind tsc --noEmit without -b or -p
            (ws / "gauntlet.toml").write_text(
                'stack = "typescript"\n\n[[layers]]\nname = "types"\ncommand = ["npx", "tsc", "--noEmit"]\n',
                encoding="utf-8",
            )

            checker = DoctorChecker()
            report = checker.check_workspace(ws)

            ts_findings = [f for f in report.findings if f.category == "TSCONFIG_PROJECT_REFERENCES"]
            self.assertGreater(len(ts_findings), 0)
            self.assertEqual(ts_findings[0].severity, FindingSeverity.WARNING)
            self.assertIn("tsc -b", ts_findings[0].remediation)
            self.assertIn("TSCONFIG_PROJECT_REFERENCES", report.migration_prompt)

    def test_doctor_passes_solution_tsconfig_with_tsc_build(self) -> None:
        """Doctor must be healthy when solution tsconfig runs tsc -b."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = Path(tmp_dir)
            ProjectScaffolder().scaffold(workspace=ws, stack="typescript")

            (ws / "tsconfig.json").write_text(
                '{\n  "files": [],\n  "references": [\n    { "path": "./tsconfig.app.json" }\n  ]\n}\n',
                encoding="utf-8",
            )
            (ws / "gauntlet.toml").write_text(
                'stack = "typescript"\n\n[[layers]]\nname = "types"\ncommand = ["npx", "tsc", "-b"]\n',
                encoding="utf-8",
            )

            checker = DoctorChecker()
            report = checker.check_workspace(ws)

            ts_findings = [f for f in report.findings if f.category == "TSCONFIG_PROJECT_REFERENCES"]
            self.assertEqual(len(ts_findings), 0)

    def test_doctor_to_dict_and_json_serialization(self) -> None:
        """Doctor report must serialize cleanly to JSON."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = Path(tmp_dir)
            ProjectScaffolder().scaffold(workspace=ws, stack="python")

            checker = DoctorChecker()
            report = checker.check_workspace(ws)
            d = report.to_dict()

            self.assertIn("healthy", d)
            self.assertIn("findings", d)
            self.assertIn("migration_prompt", d)
            dumped = json.dumps(d)
            self.assertIsInstance(dumped, str)


if __name__ == "__main__":
    unittest.main()

