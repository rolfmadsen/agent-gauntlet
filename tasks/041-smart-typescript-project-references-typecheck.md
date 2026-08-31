---
type: Task Package
title: 'Task 041: Smart TypeScript Project References & Full Typecheck Detection'
description: 'Udvide TypeScript stack-detektering og profiles til automatisk at identificere Project References / Solution Style tsconfigs (tsconfig.app.json / references) og generere npx tsc -b eller -p, samt tilføje agent-gauntlet doctor advarsel mod blind tsc --noEmit.'
status: stable
tags:
- task
- typescript
- tsconfig
- project-references
- doctor
- gauntlet
- scaffolding
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-31T15:36:00Z'
verified:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-31T15:46:00Z'
  note: 'Alle lag passeret inkl. test_stacks, test_doctor, test_scaffold og 62/62 mutanter killed'
---

# Task 041: Smart TypeScript Project References & Full Typecheck Detection

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-31`  

## 🎯 Formål
Forhindre at fejl i TypeScript-kodebaser slipper uopdaget forbi verifikationslaget på grund af Solution Style / Project References konfigurering (`tsconfig.json` med `"files": []` og `"references": [...]`):
1. **Smart TypeScript Layer Generator (`src/agent_gauntlet/features/stacks/`)**:
   - Automatisk inspicere `tsconfig.json` og tilstødende konfigurationer (`tsconfig.app.json`, `tsconfig.node.json`).
   - Generere `["npx", "tsc", "-b"]` (eller `["npx", "tsc", "--noEmit", "-p", "tsconfig.app.json"]`) i stedet for blind `["npx", "tsc", "--noEmit"]`, når composite/solution konfigurationer detekteres.
   - Robust parsing af JSONC (JSON with comments og trailing commas) i `tsconfig.json`.
2. **Agent-Gauntlet Doctor Check (`src/agent_gauntlet/features/doctor/`)**:
   - Tilføje validering i `agent-gauntlet doctor`, der advarer med `TSCONFIG_PROJECT_REFERENCES`, hvis et projekt benytter project references, men `gauntlet.toml` kun kører `tsc --noEmit` uden `-b` eller `-p`.
   - Generere automatisk udbedringsvejledning i doctor migration prompten.
3. **Opdatering af Bundled Skills, Skabeloner & Kodestandarder**:
   - Opdatere `templates/root/.agents/AGENTS.md`, `templates/plugin/agent-gauntlet/skills/old-coder/references/gauntlet.md` og `CODING_STANDARDS.md` (samt `CODING_STANDARDS_TYPESCRIPT` i `scaffolder.py`) med klare retningslinjer for TypeScript solution configs.
4. **Verifikation & Mutanter**:
   - Skrive dækkende unit- og integrationstests i `tests/features/test_stacks.py`, `tests/features/test_doctor.py` og `tests/features/test_scaffold.py`.
   - Tilføje syntetiske mutanter i `tools/mutants.py` og opnå 100% kill-rate.

## 📋 Acceptance Criteria
- [x] **Smart TypeScript Inspection (`src/agent_gauntlet/features/stacks/detector.py`)**:
  - [x] Implementere `has_typescript_project_references(workspace_path: Path | str) -> bool` med JSONC og kommentar-resistent parsing.
  - [x] Implementere `get_typescript_typecheck_command(workspace_path: Path | str | None = None) -> list[str]`.
  - [x] Returnere `["npx", "tsc", "-b"]` når `tsconfig.json` indeholder `references` eller når `tsconfig.app.json` + `tsconfig.node.json` findes med solution tsconfig.
  - [x] Returnere `["npx", "tsc", "--noEmit", "-p", "tsconfig.app.json"]` når `tsconfig.app.json` findes uden root references.
  - [x] Returnere `["npx", "tsc", "--noEmit"]` for standard single-tsconfig projekter eller når ingen `workspace_path` er givet.
- [x] **Profile & Config Loader Integration (`profiles.py`, `loader.py`, `scaffolder.py`)**:
  - [x] `get_typescript_default_layers(workspace_path=...)` anvender den detekterede typecheck-kommando.
  - [x] `get_default_stack_profile("typescript", workspace_path=...)` videresender `workspace_path`.
  - [x] `generate_default_config_toml("typescript", workspace_path=...)` og `generate_default_config_json` anvender den dynamisk detekterede typecheck-kommando.
  - [x] `ProjectScaffolder.scaffold()` overfører target `workspace` til config generatorerne.
- [x] **Doctor Integrity Check (`src/agent_gauntlet/features/doctor/checker.py`)**:
  - [x] `DoctorChecker` advarer (`FindingSeverity.WARNING`, kategori `TSCONFIG_PROJECT_REFERENCES`), hvis project references detekteres, men `gauntlet.toml` / `gauntlet.json` kører `tsc --noEmit` uden `-b` eller `-p`.
  - [x] `DoctorChecker._generate_migration_prompt` inkluderer udbedringsinstruktion til at opdatere `gauntlet.toml`.
- [x] **Skabeloner & Kodestandarder**:
  - [x] Opdatere `old-coder/references/gauntlet.md` med TypeScript solution style advarsel og vejledning.
  - [x] Opdatere `CODING_STANDARDS.md` og `CODING_STANDARDS_TYPESCRIPT` i `scaffolder.py` med typecheck-invarianter.
  - [x] Synkronisere alle skabeloner på tværs af `templates/`, `src/agent_gauntlet/templates/`, `packages/agent-gauntlet/` og `.agents/`.
- [x] **Gauntlet & Mutation Testing**:
  - [x] Unit tests i `tests/features/test_stacks.py`, `tests/features/test_doctor.py`, `tests/features/test_scaffold.py`.
  - [x] Tilføje mutanter i `tools/mutants.py` og opnå 100% kill-rate (62/62 mutanter).
  - [x] Fuld gauntlet verifikation (`PYTHONPATH=src python3 -m unittest discover tests`, `python3 tools/mutants.py`, `agent-gauntlet okf validate`).

## 🚫 Must NOT
- Må IKKE fejle eller kaste unhandled exceptions, hvis `tsconfig.json` indeholder syntaktiske kommentarer (`//` eller `/* */`) eller trailing commas.
- Må IKKE ændre standardadfærd for single-project TypeScript projekter (de skal fortsat anvende `["npx", "tsc", "--noEmit"]`).
- Må IKKE overskride `cli.py` Slim Dispatcher budgettet (maks. 300 linjer).

## 📝 Revisions
- 2026-08-31: Oprettet specifikation for Task 041 efter opdagelse af silent false-positive typechecks i Solution Style TypeScript projekter.
- 2026-08-31: Implementeret detektion, profile generator, doctor check, skabeloner og 62/62 mutanter.
