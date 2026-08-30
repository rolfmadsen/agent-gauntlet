"""Workspace integrity and duplicate scanner engine for agent-gauntlet doctor."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from agent_gauntlet.features.doctor.models import (
    DoctorFinding,
    DoctorReport,
    FindingSeverity,
)

REQUIRED_OLD_CODER_REFS: Sequence[str] = (
    "verifier.md",
    "templates.md",
    "gauntlet.md",
    "verifier-case-study.md",
)


class DoctorChecker:
    """Performs non-destructive, read-only integrity and duplicate analysis on a workspace."""

    def check_workspace(self, workspace: Path) -> DoctorReport:
        """Audits the workspace and returns a consolidated DoctorReport.

        Args:
            workspace: Root directory of the target workspace.

        Returns:
            DoctorReport detailing all findings and generated migration guidance.
        """
        root = workspace.resolve()
        findings: list[DoctorFinding] = []

        # 1. Root configuration & documentation checks
        self._check_root_documents(root, findings)

        # 2. Stray task files & shadow specifications
        self._check_stray_and_shadow_files(root, findings)

        # 3. Plugin bundle & skill integrity
        self._check_plugin_and_skill_integrity(root, findings)

        # 4. Duplicate skills & third-party stubs
        self._check_duplicate_skills(root, findings)

        has_errors = any(f.severity == FindingSeverity.ERROR for f in findings)
        healthy = len(findings) == 0

        migration_prompt = self._generate_migration_prompt(root, findings)

        return DoctorReport(
            workspace=str(root),
            healthy=healthy,
            has_errors=has_errors,
            findings=findings,
            migration_prompt=migration_prompt,
        )

    def _check_root_documents(self, root: Path, findings: list[DoctorFinding]) -> None:
        """Verifies presence of core project governance documents."""
        if not (root / "spec.md").is_file():
            findings.append(
                DoctorFinding(
                    severity=FindingSeverity.ERROR,
                    category="MISSING_FILE",
                    path="spec.md",
                    message="Macro system specification 'spec.md' is missing in workspace root.",
                    remediation="Run 'agent-gauntlet init' or create spec.md following OKF v0.2 standard.",
                )
            )

        if not (root / "CONTEXT.md").is_file():
            findings.append(
                DoctorFinding(
                    severity=FindingSeverity.ERROR,
                    category="MISSING_FILE",
                    path="CONTEXT.md",
                    message="Domain language glossary 'CONTEXT.md' is missing in workspace root.",
                    remediation="Run 'agent-gauntlet init' or create CONTEXT.md with Aristotle genus/differentia glossary.",
                )
            )

        if not (root / "gauntlet.toml").is_file() and not (root / "gauntlet.json").is_file():
            findings.append(
                DoctorFinding(
                    severity=FindingSeverity.ERROR,
                    category="MISSING_FILE",
                    path="gauntlet.toml",
                    message="Gauntlet multi-stack configuration file ('gauntlet.toml' or 'gauntlet.json') is missing.",
                    remediation="Run 'agent-gauntlet init' to generate configuration.",
                )
            )

        if not (root / "CODING_STANDARDS.md").is_file():
            findings.append(
                DoctorFinding(
                    severity=FindingSeverity.WARNING,
                    category="MISSING_FILE",
                    path="CODING_STANDARDS.md",
                    message="Language and architecture standards 'CODING_STANDARDS.md' is missing.",
                    remediation="Run 'agent-gauntlet init' to scaffold stack coding standards.",
                )
            )

        tasks_dir = root / "tasks"
        if not tasks_dir.is_dir():
            findings.append(
                DoctorFinding(
                    severity=FindingSeverity.ERROR,
                    category="MISSING_DIR",
                    path="tasks/",
                    message="Task management directory 'tasks/' is missing.",
                    remediation="Create 'tasks/' directory and place numbered task files (e.g. tasks/001-bootstrap.md) inside.",
                )
            )
        else:
            task_files = list(tasks_dir.glob("*.md"))
            if not task_files:
                findings.append(
                    DoctorFinding(
                        severity=FindingSeverity.WARNING,
                        category="EMPTY_DIR",
                        path="tasks/",
                        message="Directory 'tasks/' contains no markdown task packages.",
                        remediation="Create an initial task package under tasks/ (e.g. tasks/001-bootstrap.md).",
                    )
                )

    def _check_stray_and_shadow_files(self, root: Path, findings: list[DoctorFinding]) -> None:
        """Detects root task.md, .agents/task.md, and shadow specifications."""
        if (root / "task.md").is_file():
            findings.append(
                DoctorFinding(
                    severity=FindingSeverity.ERROR,
                    category="STRAY_FILE",
                    path="task.md",
                    message="Legacy root 'task.md' detected. In agent-gauntlet, all tasks must be tracked in 'tasks/0xx-*.md'.",
                    remediation="Move root 'task.md' into 'tasks/' as a numbered task file (e.g. 'tasks/001-bootstrap.md') and delete root 'task.md'.",
                )
            )

        if (root / ".agents" / "task.md").is_file():
            findings.append(
                DoctorFinding(
                    severity=FindingSeverity.ERROR,
                    category="STRAY_FILE",
                    path=".agents/task.md",
                    message="Stray 'task.md' detected inside '.agents/'. Tasks must reside exclusively in 'tasks/'.",
                    remediation="Move '.agents/task.md' into 'tasks/' and delete '.agents/task.md'.",
                )
            )

        shadow_specs = [
            root / ".agents" / "spec.md",
            root / "docs" / "spec.md",
        ]
        for spec_p in shadow_specs:
            if spec_p.is_file():
                rel = str(spec_p.relative_to(root))
                findings.append(
                    DoctorFinding(
                        severity=FindingSeverity.WARNING,
                        category="SHADOW_SPEC",
                        path=rel,
                        message=f"Shadow specification detected at '{rel}'. Canonical specification is 'spec.md' in root.",
                        remediation=f"Consolidate domain invariants into root 'spec.md' and remove '{rel}'.",
                    )
                )

        if (root / ".agents" / "CONTEXT.md").is_file():
            findings.append(
                DoctorFinding(
                    severity=FindingSeverity.WARNING,
                    category="SHADOW_GLOSSARY",
                    path=".agents/CONTEXT.md",
                    message="Shadow glossary detected at '.agents/CONTEXT.md'. Canonical glossary is 'CONTEXT.md' in root.",
                    remediation="Consolidate terminology into root 'CONTEXT.md' and remove '.agents/CONTEXT.md'.",
                )
            )

    def _check_plugin_and_skill_integrity(self, root: Path, findings: list[DoctorFinding]) -> None:
        """Verifies completeness of agent-gauntlet plugin and bundled skill references."""
        plugin_dir = root / ".agents" / "plugins" / "agent-gauntlet"
        skills_dir = root / ".agents" / "skills"

        # Check plugin structure if plugin directory exists
        if plugin_dir.is_dir():
            if not (plugin_dir / "plugin.json").is_file():
                findings.append(
                    DoctorFinding(
                        severity=FindingSeverity.ERROR,
                        category="PLUGIN_DEFECT",
                        path=".agents/plugins/agent-gauntlet/plugin.json",
                        message="Missing plugin manifest 'plugin.json' in agent-gauntlet plugin directory.",
                        remediation="Run 'agent-gauntlet init --force' to restore plugin manifest.",
                    )
                )
            if not (plugin_dir / "hooks.json").is_file():
                findings.append(
                    DoctorFinding(
                        severity=FindingSeverity.WARNING,
                        category="PLUGIN_DEFECT",
                        path=".agents/plugins/agent-gauntlet/hooks.json",
                        message="Missing 'hooks.json' in agent-gauntlet plugin directory.",
                        remediation="Run 'agent-gauntlet init --force' to restore hook configuration.",
                    )
                )

        # Inspect old-coder references in plugin or skills
        old_coder_dirs = [
            plugin_dir / "skills" / "old-coder",
            skills_dir / "old-coder",
        ]
        target_oc = next((d for d in old_coder_dirs if d.is_dir()), None)
        if target_oc:
            rel_prefix = str(target_oc.relative_to(root))
            if not (target_oc / "SKILL.md").is_file():
                findings.append(
                    DoctorFinding(
                        severity=FindingSeverity.ERROR,
                        category="SKILL_INCOMPLETE",
                        path=f"{rel_prefix}/SKILL.md",
                        message=f"Missing SKILL.md in '{rel_prefix}'.",
                        remediation="Run 'agent-gauntlet init --force' to restore complete skill definition.",
                    )
                )

            refs_dir = target_oc / "references"
            if not refs_dir.is_dir():
                findings.append(
                    DoctorFinding(
                        severity=FindingSeverity.ERROR,
                        category="SKILL_INCOMPLETE",
                        path=f"{rel_prefix}/references/",
                        message=f"Critical dependency directory '{rel_prefix}/references/' is missing.",
                        remediation="Run 'agent-gauntlet init --force' to copy the complete references subtree.",
                    )
                )
            else:
                for ref_name in REQUIRED_OLD_CODER_REFS:
                    ref_p = refs_dir / ref_name
                    if not ref_p.is_file() or ref_p.stat().st_size == 0:
                        findings.append(
                            DoctorFinding(
                                severity=FindingSeverity.ERROR,
                                category="SKILL_INCOMPLETE",
                                path=f"{rel_prefix}/references/{ref_name}",
                                message=f"Critical old-coder reference '{rel_prefix}/references/{ref_name}' is missing or empty.",
                                remediation="Run 'agent-gauntlet init --force' to install full reference documents.",
                            )
                        )

        # Inspect diagnose skill
        diagnose_dirs = [
            plugin_dir / "skills" / "diagnose",
            skills_dir / "diagnose",
        ]
        target_diag = next((d for d in diagnose_dirs if d.is_dir()), None)
        if target_diag:
            diag_skill = target_diag / "SKILL.md"
            if diag_skill.is_file():
                if diag_skill.stat().st_size < 300:
                    rel_s = str(diag_skill.relative_to(root))
                    findings.append(
                        DoctorFinding(
                            severity=FindingSeverity.WARNING,
                            category="SKILL_TRUNCATED",
                            path=rel_s,
                            message=f"Skill '{rel_s}' appears to be a truncated stub instead of the full 6-step root-cause model.",
                            remediation="Run 'agent-gauntlet init --force' to install the authoritative diagnose skill.",
                        )
                    )

    def _check_duplicate_skills(self, root: Path, findings: list[DoctorFinding]) -> None:
        """Scans for duplicate skills between plugin and loose .agents/skills/ directory."""
        plugin_skills_dir = root / ".agents" / "plugins" / "agent-gauntlet" / "skills"
        local_skills_dir = root / ".agents" / "skills"

        if plugin_skills_dir.is_dir() and local_skills_dir.is_dir():
            plugin_skills = {p.name for p in plugin_skills_dir.iterdir() if p.is_dir()}
            local_skills = {p.name for p in local_skills_dir.iterdir() if p.is_dir()}
            duplicates = plugin_skills.intersection(local_skills)

            for dup in sorted(duplicates):
                findings.append(
                    DoctorFinding(
                        severity=FindingSeverity.WARNING,
                        category="DUPLICATE_SKILL",
                        path=f".agents/skills/{dup}",
                        message=f"Duplicate skill '{dup}' found in '.agents/skills/'. This skill is already bundled in '.agents/plugins/agent-gauntlet/skills/'.",
                        remediation=f"Remove redundant loose directory '.agents/skills/{dup}' to avoid configuration shadowing.",
                    )
                )

        # Check for known redundant third-party alias stubs
        if local_skills_dir.is_dir():
            redundant_aliases = {
                "diagnosing-bugs": "diagnose",
                "grilling": "grill-me",
            }
            for alias, canonical in redundant_aliases.items():
                alias_dir = local_skills_dir / alias
                if alias_dir.is_dir():
                    findings.append(
                        DoctorFinding(
                            severity=FindingSeverity.WARNING,
                            category="REDUNDANT_SKILL",
                            path=f".agents/skills/{alias}",
                            message=f"Redundant skill alias '{alias}' found. Use canonical '{canonical}' instead.",
                            remediation=f"Remove '.agents/skills/{alias}' in favor of canonical '{canonical}'.",
                        )
                    )

    def _generate_migration_prompt(self, root: Path, findings: list[DoctorFinding]) -> str:
        """Generates a tailored AI migration and remediation prompt."""
        if not findings:
            return ""

        commands: list[str] = []
        instructions: list[str] = []

        # Stray task.md fixes
        if (root / "task.md").is_file():
            instructions.append(
                "1. **Migrate Root Task**: Move `task.md` into `tasks/001-bootstrap.md` (or relevant number) and delete root `task.md`."
            )
            commands.append("mkdir -p tasks")
            commands.append("mv task.md tasks/001-bootstrap.md")

        if (root / ".agents" / "task.md").is_file():
            instructions.append(
                "2. **Remove Stray Task in .agents**: Remove `.agents/task.md` after copying any active criteria into `tasks/`."
            )
            commands.append("rm .agents/task.md")

        # Shadow specs
        if (root / ".agents" / "spec.md").is_file():
            instructions.append(
                "3. **Remove Shadow Spec**: Delete shadow specification `.agents/spec.md`."
            )
            commands.append("rm .agents/spec.md")

        # Missing references or plugin structure
        has_missing_refs = any(
            "references" in f.path
            or f.category in ("MISSING_FILE", "SKILL_INCOMPLETE", "PLUGIN_DEFECT")
            for f in findings
        )
        if has_missing_refs:
            instructions.append(
                "4. **Restore Canonical Plugin Tree & References**: Run `agent-gauntlet init --force` to copy all skills, hooks, and references (`references/verifier.md`, `references/templates.md`, `references/gauntlet.md`)."
            )
            commands.append("agent-gauntlet init --force")

        # Duplicate skills
        dup_findings = [f for f in findings if f.category in ("DUPLICATE_SKILL", "REDUNDANT_SKILL")]
        if dup_findings:
            instructions.append(
                "5. **Clean Up Duplicate/Redundant Skills**: Remove loose duplicate skills in `.agents/skills/`:"
            )
            for df in dup_findings:
                commands.append(f"rm -rf {df.path}")

        prompt_lines = [
            "# AI Migration & Clean-up Plan for agent-gauntlet",
            "",
            "Please execute the following workspace cleanup and migration steps to restore 100% integrity to the agent-gauntlet architecture:",
            "",
            "## 📋 Recommended Actions",
        ]
        prompt_lines.extend(instructions)
        prompt_lines.append("")
        prompt_lines.append("## ⚡ Shell Execution Commands")
        prompt_lines.append("```bash")
        prompt_lines.extend(commands)
        prompt_lines.append("agent-gauntlet doctor")
        prompt_lines.append("agent-gauntlet verify")
        prompt_lines.append("```")

        return "\n".join(prompt_lines)
