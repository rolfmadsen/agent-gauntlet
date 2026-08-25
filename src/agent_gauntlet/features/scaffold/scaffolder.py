"""Project Scaffolder engine for agent-gauntlet."""

from __future__ import annotations

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
from agent_gauntlet.features.stacks.detector import detect_stack

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
> 📋 [Task](tasks/) • 📖 [Glossary](CONTEXT.md) • 🏛️ [ADR](docs/adr/) • 🧪 [Evidence](evidence.md)

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

---

## 🗂️ Task Management Protocol (`tasks/`)
1. **Curated Scope:** Every non-trivial work item is tracked as a concise markdown file in `tasks/<number>-<title>.md`.
2. **OKF v0.2 Frontmatter Governance:**
   * **In SPEC phase:** Agent creates task with `generated: { by: <harness>/<model>, at: <iso> }` and `status: draft`.
   * **In DONE phase:** `agent-gauntlet verify` automatically stamps `verified: { by: process:agent-gauntlet-verify, at: <iso> }` and `status: stable`.
   * **Manual Human Review:** If manually verified by a human, stamp `verified: { by: human:maintainer, at: <iso> }`.
   * **Zero Fake Signoffs:** An agent must NEVER stamp `by: human:...` on code it wrote and tested itself; automated testing is always attributed honestly to `process:agent-gauntlet-verify`.
3. **Standard Task Structure:**
   * `# Task <number>: <Title>` (Header with `Status: ACTIVE | DONE`, `Intent: 🚀 NEW FEATURE | 🐛 BUG FIX | 🔄 REFACTOR`)
   * `## 🎯 Formål`: Konkret målsætning og afgrænsning.
   * `## 📋 Acceptance Criteria`: Eksekverbare `- [ ]` punkter med klare forventede inputs og outputs.
   * `## 🚫 Must NOT`: Negative begrænsninger og arkitektur-invarianter, der under ingen omstændigheder må brydes.
   * `## 📝 Revisions`: Append-only ændringslog for mid-task ændringer og afviste forslag (hvad brugeren sagde nej til).
   * `## 🧪 Verifikation`: Konkrete kommandoer til afprøvning og validering.
4. **Clean Session Handoffs:** A new chat session starts by reading the designated `tasks/<task>.md` and `CONTEXT.md`.
5. **No Memory Rot:** Completed tasks are marked `DONE` and remain frozen; persistent domain knowledge is distilled into `CONTEXT.md` and `docs/adr/`.


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
   - Source-State Tree Digest
6. **EVIDENCE**: Persist cryptographically signed evidence ledger in `evidence.json` and `evidence.md`.
7. **SESSION HANDOFF**: Display the clean `🏁 SESSION HANDOFF` card (Variant A) with the copy-paste starter prompt in the final user-facing response:
   > ### 🏁 SESSION HANDOFF • `<task_id>`
   > **Status**: `TASK: DONE` | **Evidens**: `FORSEGLET (HMAC-SHA256)` | **Context**: `Fresh Session Recommended`
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


DEFAULT_HOOKS_JSON = """{
  "pre_tool_invocation": {
    "command": ["python3", "-m", "agent_gauntlet.features.adapters.antigravity.hook"]
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


class ProjectScaffolder:
    """Orchestrates non-destructive initialization of an agent-gauntlet workspace."""

    def __init__(self, source_skills_dir: Path | None = None) -> None:
        self.source_skills_dir = source_skills_dir

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
                return ScaffoldEntry(path=rel_path, status=ScaffoldStatus.OVERWRITTEN, description=description)
            return ScaffoldEntry(path=rel_path, status=ScaffoldStatus.SKIPPED, description=f"{description} (already exists)")

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return ScaffoldEntry(path=rel_path, status=ScaffoldStatus.CREATED, description=description)

    def scaffold(
        self,
        workspace: Path,
        stack: str | None = None,
        harness: str = "antigravity",
        config_format: str = "toml",
        force: bool = False,
    ) -> ScaffoldResult:
        """Scaffolds all essential files and folders in workspace."""
        if harness not in SUPPORTED_HARNESSES:
            raise ValueError(
                f"Unsupported harness '{harness}'. Supported harnesses: {', '.join(SUPPORTED_HARNESSES)}"
            )

        chosen_stack = stack or detect_stack(workspace) or "python"
        result = ScaffoldResult(workspace=workspace, stack=chosen_stack, harness=harness)

        # 1. Config file
        config_name = f"gauntlet.{config_format}"
        config_content = (
            generate_default_config_json(chosen_stack)
            if config_format == "json"
            else generate_default_config_toml(chosen_stack)
        )
        result.entries.append(
            self._write_file_safely(
                workspace / config_name,
                config_content,
                f"Multi-stack gauntlet configuration for '{chosen_stack}'",
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

        # 3. Tasks directory & initial task
        result.entries.append(
            self._write_file_safely(
                workspace / "tasks/001-bootstrap.md",
                DEFAULT_BOOTSTRAP_TASK,
                "Starter task template",
                force,
            )
        )

        # 4. ADR directory & initial ADR
        result.entries.append(
            self._write_file_safely(
                workspace / "docs/adr/README.md",
                DEFAULT_ADR_README,
                "Architecture Decision Record README",
                force,
            )
        )
        result.entries.append(
            self._write_file_safely(
                workspace / "docs/adr/0001-initial-architecture.md",
                DEFAULT_ADR_0001,
                "Initial architectural baseline record",
                force,
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

        # 6. Bundled skills in .agents/skills/
        skills_map = {
            ".agents/skills/old-coder/SKILL.md": (SKILL_OLD_CODER, "Evidence-first development skill"),
            ".agents/skills/grill-me/SKILL.md": (SKILL_GRILL_ME, "Socratic interview sparring skill"),
            ".agents/skills/grill-with-docs/SKILL.md": (SKILL_GRILL_WITH_DOCS, "Domain model & ADR sparring skill"),
            ".agents/skills/diagnose/SKILL.md": (SKILL_DIAGNOSE, "Disciplined diagnosis loop skill"),
        }

        # If source skills directory is provided or exists in repo, copy them
        installed_skills_dir = None
        if self.source_skills_dir and self.source_skills_dir.is_dir():
            installed_skills_dir = self.source_skills_dir
        else:
            repo_skills = Path(__file__).resolve().parent.parent.parent.parent / ".agents/skills"
            if repo_skills.is_dir():
                installed_skills_dir = repo_skills

        for skill_rel_path, (default_content, skill_desc) in skills_map.items():
            target_skill_file = workspace / skill_rel_path
            content_to_write = default_content
            if installed_skills_dir:
                source_file = installed_skills_dir / Path(skill_rel_path).relative_to(".agents/skills")
                if source_file.is_file():
                    try:
                        content_to_write = source_file.read_text(encoding="utf-8")
                    except Exception:
                        content_to_write = default_content

            result.entries.append(
                self._write_file_safely(
                    target_skill_file,
                    content_to_write,
                    skill_desc,
                    force,
                )
            )

        return result
