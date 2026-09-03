"""Project Scaffolder engine for agent-gauntlet."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from agent_gauntlet.features.adapters import SUPPORTED_HARNESSES
from agent_gauntlet.features.config.loader import (
    generate_default_config_json,
    generate_default_config_toml,
)
from agent_gauntlet.features.scaffold.models import (
    ScaffoldEntry,
    ScaffoldResult,
    ScaffoldStatus,
)
from agent_gauntlet.features.scaffold.standards import (
    generate_coding_standards,
    normalize_stacks,
)
from agent_gauntlet.features.stacks.detector import detect_stacks

DEFAULT_CONTEXT_MD = """---
type: Knowledge Bundle Index
title: Domain Language Glossary (CONTEXT.md)
description: Canonical domain vocabulary and definitions using Aristotle's formula
status: stable
generated: { by: process:agent-gauntlet-init, at: "2026-08-23T12:00:00Z" }
tags: [glossary, domain-model, ubiquitous-language, okf]
---

# Domain Language Glossary (CONTEXT.md)

This file defines the canonical domain vocabulary for the repository using Aristotle's formula (*definitio per genus et differentiam*):
- **Formula**: "A [Term] is a [Genus], that [Differentia]."
- **Pure Semantics**: Describe what a domain concept *is*, not how it is implemented in code.

---

## Core Domain Terms

### [ExampleTerm]
A [Genus], that [Differentia].
"""

DEFAULT_SPEC_MD = """---
type: System Specification
title: Specification - System Architecture & Capabilities
description: Macro system architecture, philosophy, and invariants
status: stable
generated: { by: process:agent-gauntlet-init, at: "2026-08-23T12:00:00Z" }
tags: [specification, architecture, invariants]
---

# Specification: System Architecture & Capabilities

## 🎯 Philosophy & Core Principles
- **Uncle Bob Clean Architecture & TDD**: Strict Red -> Green -> Refactor discipline.
- **Deterministic Cryptographic Evidence**: Multi-layer verification sealed with canonical workspace manifest and detached CI attestations.

---

## 📐 Architecture & Feature Modules
- Moduler og pakkestruktur (`Package-by-Feature`).

---

## 🚫 Must NOT (System Invariants)
- Må IKKE introducere udokumenterede afhængigheder.
- Må IKKE foretage utilsigtede remote publication kommandoer (`git push`).

---

## 🧪 Multi-Layer Verification Contracts
- [ ] 100% test pass rate på tværs af unit- og feature-suiter.
- [ ] 100% mutation kill-rate.
"""

DEFAULT_BOOTSTRAP_TASK = """---
type: Task Package
title: "Task 001: Initial Project Bootstrap & Setup"
description: Etablere initial projektstruktur og køre første grønne gauntlet
status: draft
generated: { by: process:agent-gauntlet-init, at: "2026-08-23T12:00:00Z" }
tags: [bootstrap, setup, gauntlet]
---

# Task 001: Initial Project Bootstrap & Setup

**Status**: `ACTIVE`
**Intent**: `🚀 NEW FEATURE`
**Oprettet**: `2026-08-22`

## 🎯 Formål
Etablere den initiale projektstruktur og køre den første grønne verifikations-gauntlet.

## 📋 Acceptance Criteria
- [ ] Konfigurere bygge- og testmiljø for projektet.
- [ ] Køre `agent-gauntlet verify` og opnå grøn status.

## 🚫 Must NOT
- Må IKKE introducere udokumenterede eksterne afhængigheder.

## 📝 Revisions
- Initial opgave oprettet ved `agent-gauntlet init`.

## 🧪 Verifikation
- `agent-gauntlet verify`
"""

DEFAULT_ADR_README = """---
type: Architecture Documentation Index
title: "Architecture Decision Records (ADRs)"
description: "Oversigt over projektets arkitekturbeslutninger og ADR-governance"
status: stable
generated: { by: process:agent-gauntlet-init, at: "2026-08-23T12:00:00Z" }
tags: [adr, architecture, index, okf]
---

# Architecture Decision Records (ADRs)

This directory contains lightweight Architecture Decision Records for the project.

- **Strict ADR Adherence**: The agent MUST strictly comply with all accepted Architecture Decision Records in `docs/adr/`.
- **Active Sparring on Conflicts**: If a proposal contradicts existing ADRs, the agent MUST immediately challenge the contradiction.
- **Lazy Creation**: Create new ADRs only for irreversible, non-obvious architectural trade-offs.
"""

DEFAULT_ADR_0001 = """---
type: Architectural Decision Record
title: "ADR 0001: Initial Architecture & Tech Stack"
description: Valg af standard pakkestruktur og flerlags verifikationsgauntlet
status: stable
generated: { by: process:agent-gauntlet-init, at: "2026-08-23T12:00:00Z" }
verified: { by: process:agent-gauntlet-init, at: "2026-08-23T12:00:00Z" }
tags: [architecture, tech-stack, adr]
---

# ADR 0001: Initial Architecture & Tech Stack

**Status**: `ACCEPTED`
**Dato**: `2026-08-22`

## Kontekst
Projektet er initialiseret med agent-gauntlet Evidence-First verifikationsmotor.

## Beslutning
Anvende standard pakkestruktur og verificere al kode gennem en flerlags gauntlet.

## Konsekvenser
- **Positivt**: Høj pålidelighed og verificerbar kode.
- **Negativt**: Kræver at tests og typer vedligeholdes kontinuerligt.
"""


DEFAULT_AGENTS_MD = """# Agent Guidelines: agent-gauntlet

This repository follows the **Evidence-First Development & Clean Craftsmanship** methodology.

---

## 📊 Standard Response HUD Protocol
Always format the top of every visible agent response with the transparent Task HUD card:
> ### 🛡️ [Task: <Task Title / Intent>] `[<Task Type>: <Phase>]`
> **Status**: `Phase: <SPEC | RED | GREEN | REFACTOR | GAUNTLET | DONE>` | `Gauntlet: <PASS | FAIL | PENDING>`
> 📋 [Task](tasks/) • 📄 [Spec](spec.md) • 📖 [Glossary](CONTEXT.md) • 🏛️ [ADR](docs/adr/) • 🧪 [Evidence](evidence.md)

---

## 🛠️ Bundled Agent Skills (`.agents/skills/`)
The agent has direct access to bundled skills located in [.agents/skills/](.agents/skills/) (and packaged under [plugins/agent-gauntlet/skills/](plugins/agent-gauntlet/skills/)). When a skill is invoked, the agent MUST view its `SKILL.md` before proceeding:

1. **[old-coder](.agents/skills/old-coder/SKILL.md)**:
   * *Purpose*: Evidence-first development methodology (SPEC $\to$ RED $\to$ GREEN $\to$ REFACTOR $\to$ GAUNTLET $\to$ EVIDENCE).
2. **[grill-me](.agents/skills/grill-me/SKILL.md)**:
   * *Purpose*: Socratic interview to stress-test designs and resolve the decision tree before writing code.
3. **[grill-with-docs](.agents/skills/grill-with-docs/SKILL.md)**:
   * *Purpose*: Challenges plans against domain concepts in [CONTEXT.md](CONTEXT.md) and creates/updates ADRs in [docs/adr/](docs/adr/).
4. **[diagnose](.agents/skills/diagnose/SKILL.md)**:
   * *Purpose*: Disciplined root-cause diagnosis loop (Reproduce $\to$ Minimize $\to$ Hypothesize $\to$ Instrument $\to$ Fix $\to$ Regression-test).
5. **[code-review](.agents/skills/code-review/SKILL.md)**:
   * *Purpose*: Two-axis review (Standards vs Spec) running parallel sub-agents with Fowler code smells baseline.

---

## 📄 Specification Governance (`spec.md`)
1. **Macro System Specification:** `spec.md` represents the repository's high-level executable specification, system-wide invariants, and capabilities (whereas `tasks/` tracks individual, isolated work packages).
2. **Standard `spec.md` Structure:**
   * `# Specification: <System / Feature Name>`
   * `## 🎯 Philosophy & Core Capabilities`: Overordnede systemegenskaber og domæneprincipper.
   * `## 📐 Architecture & Feature Modules`: Modul- og pakkestruktur (`Package-by-Feature`).
   * `## 🚫 Must NOT (System Invariants)`: Globale sikkerheds- og arkitektur-invarianter, der gælder på tværs af alle opgaver.
   * `## 🧪 Multi-Layer Verification Contracts`: Makro-verifikationskriterier og test-dækning.
3. **Hvornår `spec.md` udfyldes & opdateres:**
   * **`🚀 NEW FEATURE` & `🔄 ARCHITECTURAL REFACTOR`:** Før kodning påbegyndes, SKAL agenten sikre, at `spec.md` er opdateret og godkendt af brugeren i SPEC-fasen.
   * **`🐛 BUG FIX` & `🔍 QUERY`:** Udføres mod de eksisterende specifikationsinvarianter uden behov for omskrivning af `spec.md`.

---

## 🗂️ Task Management Protocol (`tasks/`)
1. **Curated Scope:** Every non-trivial work item is tracked as a concise markdown file in `tasks/<number>-<title>.md`.
2. **Standard Task Structure:**
   * `# Task <number>: <Title>` (Header with `Status: ACTIVE | DONE`, `Intent: 🚀 NEW FEATURE | 🐛 BUG FIX | 🔄 REFACTOR`)
   * `## 🎯 Formål`: Konkret målsætning og afgrænsning.
   * `## 📋 Acceptance Criteria`: Eksekverbare `- [ ]` punkter med klare forventede inputs og outputs.
   * `## 🚫 Must NOT`: Negative begrænsninger og arkitektur-invarianter, der under ingen omstændigheder må brydes.
   * `## 📝 Revisions`: Append-only ændringslog for mid-task ændringer og afviste forslag (hvad brugeren sagde nej til).
   * `## 🧪 Verifikation`: Konkrete kommandoer til afprøvning og validering.
3. **Clean Session Handoffs:** A new chat session starts by reading the designated `tasks/<task>.md` and `CONTEXT.md`.
4. **No Memory Rot:** Completed tasks are marked `DONE` and remain frozen; persistent domain knowledge is distilled into `CONTEXT.md` and `docs/adr/`.

---

## 🏛️ Architecture Decisions & ADR Governance (`docs/adr/`)
1. **Strict ADR Adherence:** The agent MUST strictly comply with all accepted Architecture Decision Records in `docs/adr/`.
2. **Active Sparring on Conflicts:** If a user prompt, new task, or proposed code contradicts existing ADRs or gauntlet invariants, the agent MUST immediately challenge the contradiction, surface the trade-off, and resolve the decision before proceeding.
3. **Lazy Creation:** New ADRs in `docs/adr/` are created only for irreversible, non-obvious trade-offs.

---

## 🎯 Intent Classification & Discovery
Before writing code, classify intent and align with domain terminology:
- 🔍 **QUERY / DIAGNOSIS:** Information request or root-cause discovery (read-only; use `diagnose`).
- 🚀 **NEW FEATURE / REFACTOR:** Run `grill-me` or `grill-with-docs` to resolve decisions and update `CONTEXT.md` before coding.
- 🐛 **BUG FIX:** Reproduce failure in a red test before changing production code.
- 🧐 **CODE REVIEW / AUDIT:** Independent two-axis evaluation of changes against repository standards and spec invariants (use `code-review`).

---

## 🔄 Core Development Loop
```text
SPEC / GRILL → (Human Approval) → RED → GREEN → REFACTOR → GAUNTLET → EVIDENCE
```

1. **SPEC / GRILL**: Concrete executable criteria in `tasks/<task>.md` and `spec.md`, aligned with `CONTEXT.md`.
2. **RED**: Write black-box acceptance tests first, prove they fail with expected behavior.
3. **GREEN**: Minimal implementation to make the tests pass.
4. **REFACTOR**: Clean up code while assertions remain frozen.
5. **GAUNTLET**: Execute multi-layer verification via `agent-gauntlet verify` / `sh tools/gauntlet.sh`:
   - Linters & Static Analysis
   - Type Checks (`pyright`, `tsc`, `cargo check`)
   - Acceptance & Unit Tests
   - Invariant & Property Tests (`hypothesis`, `proptest`)
   - Mutation Testing Gauntlet (`mutants.py`)
6. **EVIDENCE**: Persist verification report in `verification-report.json` and `evidence.md`.
7. **SESSION HANDOFF**: Display the clean `🏁 SESSION HANDOFF` card with the copy-paste starter prompt and inferred engineering role in the final user-facing response:
   > ### 🏁 SESSION HANDOFF • `<task_id>`
   > **Status**: `TASK: DONE` | **Evidens**: `FORSEGLET (Two-Tier Model)` | **Næste Rolle**: `<inferred_role>`
   > 💡 *Start venligst en frisk chat-session for at bevare et skarpt kontekstvindue uden context rot.*
   >
   > 📋 **Kopiér og indsæt følgende starter-prompt i en ny chat:**
   > ```text
   > <handoff_prompt>
   > ```
"""


DEFAULT_CLAUDE_MD = """# Claude Code Guidelines: agent-gauntlet

> This repository is governed by the **agent-gauntlet** Evidence-First Development & Clean Craftsmanship methodology.
> The canonical project rules, response protocols, and domain instructions are defined in [.agents/AGENTS.md](.agents/AGENTS.md).
"""

DEFAULT_CURSOR_MDC = """---
description: "agent-gauntlet high-assurance evidence-first rules and guidelines"
globs: "*"
alwaysApply: true
---

# Cursor AI Guidelines: agent-gauntlet

> This repository is governed by the **agent-gauntlet** Evidence-First Development & Clean Craftsmanship methodology.
> The canonical project rules, response protocols, and domain instructions are defined in [.agents/AGENTS.md](.agents/AGENTS.md) and [CODING_STANDARDS.md](CODING_STANDARDS.md).
"""

DEFAULT_CURSORRULES = """# Cursor AI Guidelines: agent-gauntlet

> This repository is governed by the **agent-gauntlet** Evidence-First Development & Clean Craftsmanship methodology.
> The canonical project rules, response protocols, and domain instructions are defined in [.agents/AGENTS.md](.agents/AGENTS.md) and [CODING_STANDARDS.md](CODING_STANDARDS.md).
"""


DEFAULT_HOOKS_JSON = """{
  "agent-gauntlet-gatekeeper": {
    "enabled": true,
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -m agent_gauntlet.features.adapters.antigravity.hook",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
"""

SKILL_GRILL_ME = """---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree.
---
# Grill Me
Interview the user about their plan, architecture, or design before writing code.
"""

SKILL_DIAGNOSE = """---
name: diagnose
description: Disciplined diagnosis loop for hard bugs and performance regressions. Reproduce -> minimise -> hypothesise -> instrument -> fix -> regression-test.
---
# Diagnose
Follow the 6-step root-cause diagnosis loop.
"""

SKILL_GRILL_WITH_DOCS = """---
name: grill-with-docs
description: Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates documentation (CONTEXT.md, ADRs) inline.
---
# Grill With Docs
Challenge plans against CONTEXT.md and create/update ADRs in docs/adr/.
"""

SKILL_OLD_CODER = """---
name: old-coder
description: Evidence-first development — surround the implementation with an executable spec and a gauntlet of constraints (tests, types, coverage, mutation).
---
# Old Coder
Execute the SPEC -> RED -> GREEN -> REFACTOR -> GAUNTLET -> EVIDENCE loop.
"""

SKILL_CODE_REVIEW = """---
name: code-review
description: Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes (Standards vs Spec) with Fowler code smells baseline.
---
# Code Review
Two-axis review of the diff between HEAD and a fixed point (Standards vs Spec).
"""
# Coding standards are imported from agent_gauntlet.features.scaffold.standards


class ProjectScaffolder:
    """Orchestrates non-destructive initialization of an agent-gauntlet workspace."""

    def __init__(
        self,
        source_skills_dir: Path | None = None,
        source_plugin_dir: Path | None = None,
    ) -> None:
        self.source_skills_dir = source_skills_dir
        self.source_plugin_dir = source_plugin_dir

    def _write_file_safely(
        self,
        target_path: Path,
        content: str,
        description: str,
        force: bool,
    ) -> ScaffoldEntry:
        """Writes a file if it does not exist, or if force is enabled."""
        rel_path = str(target_path)
        if target_path.exists():
            if force:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(content, encoding="utf-8")
                return ScaffoldEntry(
                    path=rel_path, status=ScaffoldStatus.OVERWRITTEN, description=description
                )
            return ScaffoldEntry(
                path=rel_path,
                status=ScaffoldStatus.SKIPPED,
                description=f"{description} (already exists)",
            )

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return ScaffoldEntry(path=rel_path, status=ScaffoldStatus.CREATED, description=description)

    def _resolve_plugin_source(self) -> Path | None:
        """Resolves the canonical source plugin directory for templates."""
        if self.source_plugin_dir and self.source_plugin_dir.is_dir():
            return self.source_plugin_dir

        pkg_root = Path(__file__).resolve().parent.parent.parent
        repo_root = pkg_root.parent.parent
        candidates = [
            pkg_root / "templates" / "plugin" / "agent-gauntlet",
            repo_root / "templates" / "plugin" / "agent-gauntlet",
            repo_root / "plugins" / "agent-gauntlet",
        ]
        for c in candidates:
            if c.is_dir():
                return c
        return None

    def scaffold(
        self,
        workspace: Path,
        stack: str | None = None,
        stacks: Sequence[str] | str | None = None,
        harness: str = "antigravity",
        config_format: str = "toml",
        force: bool = False,
    ) -> ScaffoldResult:
        """Scaffolds all essential files and folders in workspace.

        Args:
            workspace: Target root directory for scaffolding.
            stack: Optional explicit single stack name or comma-separated string ('python', 'typescript', 'rust').
            stacks: Optional sequence or comma-separated string of stack names.
            harness: Target AI agent harness ('antigravity' or 'claude-code'). Defaults to 'antigravity'.
            config_format: Gauntlet config format ('toml' or 'json'). Defaults to 'toml'.
            force: If True, overwrites existing files. Defaults to False.

        Returns:
            ScaffoldResult containing summary of created, skipped, or overwritten entries.

        Raises:
            ValueError: If an unsupported harness name is provided.
        """
        if harness not in SUPPORTED_HARNESSES:
            raise ValueError(
                f"Unsupported harness '{harness}'. Supported harnesses: {', '.join(SUPPORTED_HARNESSES)}"
            )

        raw_input = stacks if stacks is not None else stack
        resolved_stacks = normalize_stacks(raw_input)
        if not resolved_stacks:
            resolved_stacks = detect_stacks(workspace)
        if not resolved_stacks:
            resolved_stacks = ["python"]

        primary_stack = resolved_stacks[0]
        result = ScaffoldResult(
            workspace=workspace,
            stack=primary_stack,
            stacks=resolved_stacks,
            harness=harness,
        )

        # 1. Config file
        config_name = f"gauntlet.{config_format}"
        config_content = (
            generate_default_config_json(primary_stack, workspace_path=workspace)
            if config_format == "json"
            else generate_default_config_toml(primary_stack, workspace_path=workspace)
        )
        result.entries.append(
            self._write_file_safely(
                workspace / config_name,
                config_content,
                f"Multi-stack gauntlet configuration for '{primary_stack}'",
                force,
            )
        )

        # 2. CONTEXT.md & spec.md & CLAUDE.md
        result.entries.append(
            self._write_file_safely(
                workspace / "CONTEXT.md",
                DEFAULT_CONTEXT_MD,
                "Domain language glossary template",
                force,
            )
        )
        result.entries.append(
            self._write_file_safely(
                workspace / "spec.md",
                DEFAULT_SPEC_MD,
                "System architecture & capability specification template",
                force,
            )
        )
        result.entries.append(
            self._write_file_safely(
                workspace / "CLAUDE.md",
                DEFAULT_CLAUDE_MD,
                "Claude Code guidance bridge pointing to .agents/AGENTS.md",
                force,
            )
        )
        active_standards = generate_coding_standards(resolved_stacks)
        stack_desc = (
            f"Polyglot coding standards for '{', '.join(resolved_stacks)}'"
            if len(resolved_stacks) > 1
            else f"Coding standards based on authoritative guidelines for '{primary_stack}'"
        )
        result.entries.append(
            self._write_file_safely(
                workspace / "CODING_STANDARDS.md",
                active_standards,
                stack_desc,
                force,
            )
        )

        # 3. Tasks directory & initial task (Strictly tasks/001-bootstrap.md, NO root task.md)
        tasks_dir = workspace / "tasks"
        has_existing_tasks = tasks_dir.is_dir() and any(tasks_dir.glob("*.md"))
        if not has_existing_tasks:
            result.entries.append(
                self._write_file_safely(
                    workspace / "tasks/001-bootstrap.md",
                    DEFAULT_BOOTSTRAP_TASK,
                    "Starter task template",
                    force,
                )
            )
        else:
            result.entries.append(
                ScaffoldEntry(
                    path=str(workspace / "tasks/001-bootstrap.md"),
                    status=ScaffoldStatus.SKIPPED,
                    description="Starter task template (existing tasks found in tasks/)",
                )
            )

        # 4. ADR directory & initial ADR
        adr_dir = workspace / "docs/adr"
        result.entries.append(
            self._write_file_safely(
                workspace / "docs/adr/README.md",
                DEFAULT_ADR_README,
                "Architecture Decision Record README",
                force,
            )
        )
        has_existing_adrs = adr_dir.is_dir() and any(
            f.name != "README.md" for f in adr_dir.glob("*.md")
        )
        if not has_existing_adrs:
            result.entries.append(
                self._write_file_safely(
                    workspace / "docs/adr/0001-initial-architecture.md",
                    DEFAULT_ADR_0001,
                    "Initial architectural baseline record",
                    force,
                )
            )
        else:
            result.entries.append(
                ScaffoldEntry(
                    path=str(workspace / "docs/adr/0001-initial-architecture.md"),
                    status=ScaffoldStatus.SKIPPED,
                    description="Initial architectural baseline record (existing ADRs found in docs/adr/)",
                )
            )

        # 5. .agents/AGENTS.md & hooks.json
        result.entries.append(
            self._write_file_safely(
                workspace / ".agents/AGENTS.md",
                DEFAULT_AGENTS_MD,
                "Agent guidelines with Response HUD & task rules",
                force,
            )
        )
        result.entries.append(
            self._write_file_safely(
                workspace / ".agents/hooks.json",
                DEFAULT_HOOKS_JSON,
                "PreInvocation hook gatekeeper configuration",
                force,
            )
        )

        # 6. Harness-specific rules and bridges
        if harness == "cursor":
            result.entries.append(
                self._write_file_safely(
                    workspace / ".cursor/rules/agent-gauntlet.mdc",
                    DEFAULT_CURSOR_MDC,
                    "Cursor rules bridge pointing to .agents/AGENTS.md",
                    force,
                )
            )
            result.entries.append(
                self._write_file_safely(
                    workspace / ".cursorrules",
                    DEFAULT_CURSORRULES,
                    "Cursor legacy rules bridge pointing to .agents/AGENTS.md",
                    force,
                )
            )

        # 7. Complete recursive plugin copying to .agents/plugins/agent-gauntlet/
        plugin_source = self._resolve_plugin_source()
        target_plugin_root = workspace / ".agents" / "plugins" / "agent-gauntlet"

        if plugin_source and plugin_source.is_dir():
            for src_file in sorted(plugin_source.rglob("*")):
                if src_file.is_file():
                    rel_p = src_file.relative_to(plugin_source)
                    dest_file = target_plugin_root / rel_p
                    try:
                        content = src_file.read_text(encoding="utf-8")
                    except Exception:
                        continue
                    result.entries.append(
                        self._write_file_safely(
                            dest_file,
                            content,
                            f"Plugin resource '{rel_p}'",
                            force,
                        )
                    )

        return result
