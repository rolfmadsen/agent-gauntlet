---
type: Task Package
title: 'Task 042: Polyglot Composite Coding Standards Generation'
description: 'Udvidelse af agent-gauntlet scaffolding til at generere sammensatte, fler-sprogede CODING_STANDARDS.md dokumenter for polyglot repositories (f.eks. TypeScript/React frontend + Python/Rust backend).'
status: stable
tags:
- task
- coding-standards
- polyglot
- multi-stack
- documentation
- scaffolding
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-31T15:40:00Z'
verified:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-31T16:00:00Z'
  tier: machine-confirmed
---

# Task 042: Polyglot Composite Coding Standards Generation

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-31`  

## 🎯 Formål
Etablere støtte for automatisk detektion, sammensætning og vedligeholdelse af sammensatte (composite/polyglot) `CODING_STANDARDS.md` dokumenter i projekter, der benytter flere programmeringssprog samtidig (fx TypeScript/React i frontend og Python eller Rust i backend/API):
1. **Multi-Stack Standard Fusionering**:
   - Strukturere `CODING_STANDARDS.md` i klare, modulære sektioner:
     - `## 1. Transversal Engineering & Architectural Principles` (TDD, Clean Architecture, Fail-Closed, Invariant-tests, Evidence-First).
     - `## 2. Frontend Standards: TypeScript & React` (Type safety, React architecture, TSDoc, DO/DON'T).
     - `## 3. Backend Standards: Python` / `Rust` (Type annotations, immutability, docstrings, DO/DON'T).
     - `## 4. Cross-Stack Boundary & Interop Invariants` (API schemas, data transfer boundaries, zero untyped JSON bridges, serialization contracts).
   - Give AI-kodningsagenter et samlet autoritativt regelsæt for hele repositoryet uden context rot eller modstridende retningslinjer.
2. **Polyglot Stack Detection (`detect_stacks`)**:
   - Automatisk detektere alle sprog i monorepos / polyglot workspaces ved at inspicere rodmappen samt undermapper (`frontend/`, `backend/`, `web/`, `api/`, `apps/*`, `packages/*`, `services/*`, `crates/*`, `src/*`).
3. **Scaffolder & CLI Support (`agent-gauntlet init --stacks typescript,python`)**:
   - Understøtte angivelse af flere stacks ved initiering (fx `--stack typescript,python` eller `--stacks typescript,rust`).
   - Opdatere `ProjectScaffolder` og udtrække en dedikeret `standards.py` generator for at overholde Single Responsibility Principle og holde moduler fokuserede.

## 📋 Acceptance Criteria
- [x] **Polyglot Stack Detection (`src/agent_gauntlet/features/stacks/detector.py`)**:
  - [x] Implementere `detect_stacks(workspace_path: Path | str) -> list[str]`, der scanner rod og undermapper for sprogindikatorer (`Cargo.toml`, `tsconfig.json`/`package.json`, `pyproject.toml` osv.).
  - [x] Bevare bagudkompatibilitet i `detect_stack()`, som returnerer den primære fundne stack.
- [x] **Komposabel Standards Generator (`src/agent_gauntlet/features/scaffold/standards.py`)**:
  - [x] Implementere `generate_coding_standards(stacks: list[str] | str) -> str`.
  - [x] For enkelt-stack genereres den skræddersyede sprogstandard.
  - [x] For polyglot/multi-stack genereres et struktureret dokument med tværgående principper, individuelle sprogsektioner (TypeScript, Python, Rust) og tværgående boundary/interop-regler med ensartet sektionsnummerering.
- [x] **Scaffolder & CLI Integration (`src/agent_gauntlet/features/scaffold/` & `cli.py`)**:
  - [x] `ProjectScaffolder.scaffold()` understøtter `stacks` (liste eller kommasepareret streng).
  - [x] `ScaffoldResult` beriges med `stacks: list[str]`.
  - [x] `agent-gauntlet init` og `scaffold` accepterer kommaseparerede stacks via `--stack` / `--stacks`.
  - [x] `src/agent_gauntlet/cli.py` overholder invarianten om strengt $< 300$ linjer.
- [x] **Gauntlet & Verification**:
  - [x] Acceptance & unit tests i `tests/features/test_scaffold.py` og `tests/features/test_stacks.py`.
  - [x] 100% grøn testsuite (`343/343` tests).
  - [x] 100% dræbte mutanter i `tools/mutants.py` (`65/65` mutanter dræbt).
  - [x] Bestået `agent-gauntlet check-release`, `check-spec`, `validate-plugin` og `doctor`.

## 🚫 Must NOT
- Må IKKE overskrive eksisterende custom kodestandarder uden `--force`.
- Må IKKE skabe modstridende formaterings- eller type-krav på tværs af sektionerne.
- Må IKKE overskride 300 linjer i `src/agent_gauntlet/cli.py`.
- Må IKKE bryde eksisterende single-stack `scaffold()` eller `init` API-kald.

## 📝 Revisions
- 2026-08-31: Oprettet som selvstændig opgave baseret på drøftelse af polyglot repositories (Option 1).
- 2026-08-31: Opdateret til ACTIVE i SPEC-fasen med detaljerede acceptkriterier for `detect_stacks`, `standards.py` og polyglot fusion.
- 2026-08-31: Færdiggjort og verificeret med 100% grønne tests og 65/65 dræbte mutanter.


