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

CODING_STANDARDS_PYTHON = '''# Coding Standards: Python

This repository follows the **Google Python Style Guide** and **PEP 8 / PEP 484** type conventions, tailored for high-assurance, testable, and AI-navigable architectures.

---

## 1. Type Annotations & Static Analysis
- **Strict Typing:** All function and method signatures MUST have explicit argument and return type annotations.
- **Modern Syntax:** Use Python 3.10+ native type syntax (`list[str]`, `dict[str, Any]`, `X | None` instead of `Optional[X]`, `Union[X, Y]`).
- **No Untyped Any:** Avoid bare `Any` in public signatures; use concrete types, type variables, or `object` with runtime type guards.

## 2. Immutability & Data Modeling
- **Value Objects:** Prefer `@dataclass(frozen=True)` or Pydantic `BaseModel(frozen=True)` for domain models and data transfer objects (DTOs).
- **Pure Functions:** Prefer stateless, side-effect-free pure functions where practical. Avoid mutable global or module-level state.
- **Default Arguments:** Never use mutable default arguments (`def foo(items=[])` is strictly forbidden; use `def foo(items: list[str] | None = None)`).

## 3. Architecture & Package Structure
- **Package-by-Feature (Screaming Architecture):** Colocate related business logic, models, services, and repositories within cohesive feature directories (`features/<feature_name>/`).
- **Dependency Inversion:** High-level policy modules must not depend directly on low-level detail/I/O modules; depend on abstractions/protocols (`typing.Protocol`).
- **No Circular Imports:** Architecture must be strictly acyclic.

## 4. Error Handling & Exceptions
- **Domain Exceptions:** Define explicit, domain-specific exception hierarchies deriving from a base project exception (`class DomainError(Exception): pass`).
- **No Bare Excepts:** Catching bare `except:` or broad `except Exception:` without re-raising or structured logging is strictly forbidden.
- **Fail-Closed:** In security or verification boundaries, unexpected states must fail closed (deny/abort) rather than swallow errors.

## 5. Documentation & Google Docstrings
- **AI-Native Documentation:** Document *Why* (invariants, architectural boundaries, edge cases) rather than restating *What* the code does. Avoid noisy line-by-line comments.
- **Module Docstrings:** Every Python module MUST start with a top-level docstring summarizing its responsibility and boundary invariants.
- **Google Docstrings Standard:** All public functions, classes, and methods MUST use structured Google-style docstrings with explicit `Args:`, `Returns:`, and `Raises:` sections.

## 6. Concrete DO / DON'T Examples

### ❌ DON'T (Anti-pattern: Untyped, mutable defaults, swallowed exceptions, noisy comments)
```python
# bad_module.py
# loop over users and get data
def get_user_data(user_id, cache={}):  # ❌ Mutable default argument
    # check if user is in cache
    try:
        return cache[user_id]
    except:  # ❌ Bare except masks bugs
        return None
```

### ✅ DO (Idiomatic: Strict types, frozen dataclass, Google docstrings, domain exceptions)
```python
"""User data access and cache management feature."""

from collections.abc import Mapping
from dataclasses import dataclass


class UserNotFoundError(Exception):
    """Raised when the requested user profile cannot be located."""


@dataclass(frozen=True)
class UserProfile:
    """Immutable domain representation of a user profile."""

    user_id: str
    email: str
    is_active: bool = True


def get_user_data(
    user_id: str,
    cache: Mapping[str, UserProfile] | None = None,
) -> UserProfile:
    """Retrieves user profile data from cache or repository.

    Args:
        user_id: Unique string identifier for the user.
        cache: Optional pre-warmed cache map. Defaults to None.

    Returns:
        The resolved immutable UserProfile.

    Raises:
        ValueError: If user_id is empty or malformed.
        UserNotFoundError: If the user profile does not exist.
    """
    if not user_id.strip():
        raise ValueError("user_id cannot be empty")

    local_cache = cache or {}
    if user_id not in local_cache:
        raise UserNotFoundError(f"User '{user_id}' not found in cache")

    return local_cache[user_id]
```
'''

CODING_STANDARDS_TYPESCRIPT = """# Coding Standards: TypeScript & React

This repository follows the **Google TypeScript Style Guide** and modern **Functional React & Clean Architecture** principles.

---

## 1. Type Safety & TypeScript Disciplines
- **Strict Mode:** Code must compile with `strict: true` and zero compiler warnings.
- **No `any`:** `any` is strictly prohibited. Use `unknown` combined with type narrowing, type predicates (`is`), or validation libraries (`zod`) at runtime I/O boundaries.
- **Interfaces vs Types:** Use `interface` for public API object shapes and extensible contracts; use `type` for unions, intersections, tuple types, and utility types.
- **Discriminated Unions:** Model state machines and mutually exclusive states using discriminated unions (e.g. `{ status: 'success'; data: T } | { status: 'error'; error: Error }`) rather than parallel optional boolean flags.

## 2. React & Component Architecture
- **Functional Components:** All components must be pure functional components with explicit props interfaces (`interface ButtonProps { ... }`).
- **Custom Hooks for Logic:** JSX templates must remain declarative presentation layers. Extract non-trivial business logic, asynchronous state, and side-effects into custom hooks (`use[Feature]`).
- **Component File Budget:** Components should stay focused and ideally under 150 lines. Decompose complex UIs into smaller, single-responsibility sub-components.
- **Pure Render & Side-Effects:** Avoid side-effects during render. All side-effects belong in `useEffect` or event handlers.

## 3. Immutability & State Management
- **Immutability First:** Prefer `const` over `let`. Never mutate props or state objects directly; use shallow copies or immutable updates.
- **Explicit Exports:** Use explicit named exports for components, functions, and types. Avoid `export default` except where required by file-system routing.
- **Readonly Parameters:** Mark parameters as `readonly` when they are not intended to be mutated.

## 4. Error Handling & Async
- **Predictable Async:** Always handle Promise rejections. Avoid unhandled floating promises (`void asyncFn()`).
- **Error Boundaries:** Wrap component sub-trees in Error Boundaries to gracefully catch rendering crashes without bringing down the entire application.

## 5. Documentation & TSDoc Standards
- **TSDoc Documentation Standard:** All exported functions, hooks, interfaces, and component props MUST be documented with TSDoc tags (`@param`, `@returns`, `@throws`, `@example`).
- **Self-Documenting Types:** Do not write comments that merely rephrase type signatures. Document semantic invariants and edge-case behavior.

## 6. Concrete DO / DON'T Examples

### ❌ DON'T (Anti-pattern: `any`, bloated component with inline async side-effects)
```tsx
// ❌ any type, mutable let, unhandled async in render
export default function UserCard(props: any) {
  let [data, setData] = React.useState<any>(null);
  React.useEffect(() => {
    fetch('/api/user/' + props.id).then(r => r.json()).then(d => setData(d));
  }, [props.id]);
  return <div>{data?.name}</div>;
}
```

### ✅ DO (Idiomatic: Typed props interface, custom hook, TSDoc, discriminated union)
```tsx
import React from 'react';

/** State model for asynchronous user profile loading. */
export type UserState =
  | { status: 'idle' | 'loading' }
  | { status: 'success'; profile: UserProfile }
  | { status: 'error'; error: Error };

export interface UserProfile {
  readonly id: string;
  readonly name: string;
  readonly email: string;
}

export interface UserCardProps {
  /** The unique user identifier to display. */
  readonly userId: string;
  /** Optional callback fired when the profile card is clicked. */
  readonly onSelect?: (userId: string) => void;
}

/**
 * Custom hook to manage user profile fetching and lifecycle state.
 *
 * @param userId - Unique identifier for the user.
 * @returns Discriminated union state representing loading, success, or error.
 */
export function useUserProfile(userId: string): UserState {
  const [state, setState] = React.useState<UserState>({ status: 'idle' });

  React.useEffect(() => {
    let isMounted = true;
    setState({ status: 'loading' });

    fetch(`/api/users/${encodeURIComponent(userId)}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load user: ${res.statusText}`);
        return res.json();
      })
      .then((profile: UserProfile) => {
        if (isMounted) setState({ status: 'success', profile });
      })
      .catch((error: Error) => {
        if (isMounted) setState({ status: 'error', error });
      });

    return () => {
      isMounted = false;
    };
  }, [userId]);

  return state;
}

/**
 * Presentational component rendering user profile details.
 */
export const UserCard: React.FC<UserCardProps> = ({ userId, onSelect }) => {
  const state = useUserProfile(userId);

  if (state.status === 'loading') return <div>Loading profile...</div>;
  if (state.status === 'error') return <div role="alert">{state.error.message}</div>;
  if (state.status !== 'success') return null;

  return (
    <article onClick={() => onSelect?.(userId)} className="user-card">
      <h3>{state.profile.name}</h3>
      <p>{state.profile.email}</p>
    </article>
  );
};
```
"""

CODING_STANDARDS_RUST = """# Coding Standards: Rust

This repository follows the **Official Rust API Guidelines (C-API-GUIDELINES)** and idiomatic Clean Rust principles.

---

## 1. Naming & Case Conventions (C-CASE)
- **Naming Conventions:**
  - `UpperCamelCase` for types and traits (e.g., `VerificationReport`, `TaskContract`).
  - `snake_case` for functions, methods, and modules (e.g., `execute_verify`, `parse_task_file`).
  - `SCREAMING_SNAKE_CASE` for constants and statics.
- **Constructors:** Use `new()` or `with_capacity()` as standard constructor names.

## 2. Error Handling & Invariants (C-GOOD-ERR)
- **Error Handling:**
  - `unwrap()` and `expect()` are strictly forbidden in production code. Use `?` operator for clean error propagation.
  - Libraries must define structured, strongly-typed errors implementing `std::error::Error` (via `thiserror`). Application binaries may use `anyhow` for top-level context.
  - Panics are acceptable only in test assertions and invariant property tests.

## 3. Ergonomics & Ownership (C-CONV, C-GENERIC)
- **Borrowing over Cloning:** Pass shared references (`&str`, `&[T]`) instead of owned types (`&String`, `&Vec<T>`) in function arguments.
- **Standard Conversions:** Implement standard conversion traits (`From`, `TryFrom`, `AsRef`) where natural conversions exist.
- **Newtype Pattern (C-NEWTYPE):** Wrap primitive types in lightweight domain structs (e.g., `struct UserId(String);`) to prevent *Primitive Obsession*.

## 4. Documentation & Tests (C-DOC)
- **Rustdoc Documentation Standard:** All public items MUST have `///` doc comments detailing purpose, `# Arguments`, `# Returns`, `# Errors`, `# Panics`, and `# Examples`.
- **Clippy Strictness:** Code must pass `cargo clippy -- -D warnings` with zero warnings.

## 5. Concrete DO / DON'T Examples

### ❌ DON'T (Anti-pattern: Production `unwrap()`, excessive cloning, primitive obsession)
```rust
// ❌ unwrap in production, taking &String instead of &str, cloning everywhere
pub fn fetch_user_name(id: &String) -> String {
    let db = open_connection().unwrap(); // ❌ Panic in production
    let user = db.query(id.clone()).unwrap();
    user.name
}
```

### ✅ DO (Idiomatic: Newtype pattern, `thiserror`, borrowing, standard doc comments)
```rust
use std::path::Path;
use thiserror::Error;

/// Structured domain error hierarchy.
#[derive(Debug, Error)]
pub enum ConfigError {
    #[error("Configuration file not found at '{0}'")]
    NotFound(String),
    #[error("Failed to parse configuration: {0}")]
    ParseError(#[from] toml::de::Error),
}

/// Strongly-typed identifier for configuration scopes.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ScopeId(String);

impl ScopeId {
    /// Creates a validated ScopeId.
    pub fn new(id: impl Into<String>) -> Result<Self, &'static str> {
        let val = id.into();
        if val.is_empty() {
            return Err("ScopeId cannot be empty");
        }
        Ok(Self(val))
    }

    /// Accesses the underlying string slice.
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// Loads and validates configuration from the specified workspace path.
///
/// # Arguments
/// * `path` - Path reference to configuration file.
///
/// # Errors
/// Returns [`ConfigError::NotFound`] if the file does not exist, or
/// [`ConfigError::ParseError`] if TOML syntax is invalid.
///
/// # Examples
/// ```rust
/// let cfg = load_config(Path::new("gauntlet.toml"))?;
/// ```
pub fn load_config(path: &Path) -> Result<String, ConfigError> {
    if !path.exists() {
        return Err(ConfigError::NotFound(path.display().to_string()));
    }
    std::fs::read_to_string(path).map_err(Into::into)
}
```
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

    def scaffold(
        self,
        workspace: Path,
        stack: str | None = None,
        harness: str = "antigravity",
        config_format: str = "toml",
        force: bool = False,
    ) -> ScaffoldResult:
        """Scaffolds all essential files and folders in workspace.

        Args:
            workspace: Target root directory for scaffolding.
            stack: Optional explicit stack name ('python', 'typescript', 'rust'). Defaults to auto-detection.
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
        standards_map = {
            "python": CODING_STANDARDS_PYTHON,
            "typescript": CODING_STANDARDS_TYPESCRIPT,
            "rust": CODING_STANDARDS_RUST,
        }
        stack_key = chosen_stack.lower().strip()
        active_standards = standards_map.get(stack_key, CODING_STANDARDS_PYTHON)
        result.entries.append(
            self._write_file_safely(
                workspace / "CODING_STANDARDS.md",
                active_standards,
                f"Coding standards based on authoritative guidelines for '{stack_key}'",
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

        # 6. Bundled skills in .agents/skills/
        skills_map = {
            ".agents/skills/old-coder/SKILL.md": (
                SKILL_OLD_CODER,
                "Evidence-first development skill",
            ),
            ".agents/skills/grill-me/SKILL.md": (
                SKILL_GRILL_ME,
                "Socratic interview sparring skill",
            ),
            ".agents/skills/grill-with-docs/SKILL.md": (
                SKILL_GRILL_WITH_DOCS,
                "Domain model & ADR sparring skill",
            ),
            ".agents/skills/diagnose/SKILL.md": (
                SKILL_DIAGNOSE,
                "Disciplined diagnosis loop skill",
            ),
            ".agents/skills/code-review/SKILL.md": (
                SKILL_CODE_REVIEW,
                "Two-axis code review skill",
            ),
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
                source_file = installed_skills_dir / Path(skill_rel_path).relative_to(
                    ".agents/skills"
                )
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
