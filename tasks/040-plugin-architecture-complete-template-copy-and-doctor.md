---
type: Task Package
title: 'Task 040: Plugin Architecture, Complete Template Copy, and Doctor Command'
description: 'Etablering af komplet template-træ under templates/plugin/ med alle references/, rekursiv atomar initiering i agent-gauntlet init, og implementering af read-only agent-gauntlet doctor med skræddersyet AI migration prompt.'
status: stable
tags:
- task
- template
- plugin
- init
- doctor
- diagnostic
- scaffolding
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-30T13:47:00Z'
verified:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-30T13:55:00Z'
---

# Task 040: Plugin Architecture, Complete Template Copy, and Doctor Command

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-30`  

## 🎯 Formål
Sikre 100% komplet, atomar og isoleret distribution og initiering af `agent-gauntlet` plugin- og templatesæt, samt levere et read-only diagnostisk værktøj (`agent-gauntlet doctor`), der afdækker huller, skyggefiler og dubletter i eksisterende workspaces og genererer en skræddersyet AI migration prompt:
1. **Komplette Skabeloner & Referencer (`templates/plugin/`)**: Etablere et komplet template-træ indeholdende alle skill-undermapper og referencer (`references/verifier.md`, `references/templates.md`, `references/gauntlet.md`, `references/verifier-case-study.md`, `scripts/hitl-loop.template.sh`, `ADR-FORMAT.md`, `CONTEXT-FORMAT.md`).
2. **Rekursiv Initiering (`agent-gauntlet init`)**: Opdatere `ProjectScaffolder` til at foretage rekursiv mappekopiering til `.agents/plugins/agent-gauntlet/` uden rod-`task.md` og med opdateret sti-manifest i `gauntlet.toml`.
3. **Read-Only Integritets- og Dublet-Scanner (`agent-gauntlet doctor`)**: Udvikle `doctor` motoren der inspicerer repositories for manglende filer, trunkerede stubs, skygge-specifikationer og dublet-skills, og udskriver en copy-paste AI migration prompt.
4. **Verifikation & Mutanter**: Oprette udtømmende unit-, acceptance- og mutation-tests for template-komplethed og doctor-diagnostik.

## 📋 Acceptance Criteria
- [x] **Template Distribution (`templates/plugin/` og `src/agent_gauntlet/templates/`)**:
  - [x] Etablere det fulde plugin template-træ med `plugin.json`, `hooks.json`, `policy.json`, og samtlige 5 skills (`old-coder`, `diagnose`, `grill-me`, `grill-with-docs`, `code-review`).
  - [x] Sikre at alle 4 reference-dokumenter i `old-coder/references/` er inkluderet med fuldt indhold.
  - [x] Sikre at `diagnose/scripts/` og `grill-with-docs/` referencefiler er inkluderet.
  - [x] Etablere standard rod-templates for `gauntlet.toml` med sti-manifest (`[paths]`).
- [x] **Rekursiv Initiering (`src/agent_gauntlet/features/scaffold/scaffolder.py`)**:
  - [x] `ProjectScaffolder.scaffold()` kopierer det fulde template-træ rekursivt til `.agents/plugins/agent-gauntlet/`.
  - [x] Må IKKE oprette en rod-`task.md` eller `.agents/task.md` (opretter udelukkende `tasks/001-bootstrap.md`).
  - [x] Bevare eksisterende filer i målet, medmindre `force=True` er angivet.
- [x] **Doctor Feature & AI Migration Prompt (`src/agent_gauntlet/features/doctor/`)**:
  - [x] Implementere `DoctorReport`, `DoctorFinding`, `FindingSeverity` og `DoctorChecker`.
  - [x] Validere integritet af nødvendige rod-filer (`spec.md`, `CONTEXT.md`, `gauntlet.toml`, `CODING_STANDARDS.md`).
  - [x] Validere at `tasks/` eksisterer og flagge stray filer som `task.md` i rod eller `.agents/`.
  - [x] Validere skill-integritet (fange manglende `references/verifier.md`, trunkerede `diagnose` stubs).
  - [x] Detektere dublet-skills mellem `.agents/skills/` og `.agents/plugins/agent-gauntlet/skills/`.
  - [x] Generere en formateret, handlingsorienteret AI migration prompt til automatisk sanering.
- [x] **CLI Integration (`src/agent_gauntlet/cli.py` & Node bootstrapper)**:
  - [x] Tilføje `doctor` subcommand til Python CLI med `--workspace` og `--json` support.
  - [x] Overholde Slim Dispatcher Contract (`cli.py` under 300 linjer).
  - [x] Opdatere `bin/agent-gauntlet.js` til at viderestille `doctor` til Python-motoren når tilgængelig.
- [x] **Gauntlet & Mutation Verification**:
  - [x] Tilføje testsuiter i `tests/features/test_doctor.py` og `tests/features/test_template_completeness.py`.
  - [x] Tilføje syntetiske mutanter for doctor og template copy i `tools/mutants.py`.
  - [x] Køre `sh tools/gauntlet.sh` med 100% grøn status og 100% kill-rate.

## 🚫 Must NOT
- Må IKKE oprette eller efterlade en rod-`task.md` eller `.agents/task.md`.
- Må IKKE modificere eller slette filer under kørsel af `agent-gauntlet doctor` (skal være 100% read-only).
- Må IKKE overskrive eksisterende brugerfiler under `init` uden eksplicit `--force`.
- Må IKKE overskride 300 linjer i `src/agent_gauntlet/cli.py`.

## 📝 Revisions
- 2026-08-30: Oprettet specifikation for Task 040 baseret på godkendt implementeringsplan for Plugin-arkitektur og Doctor-kommando.

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest tests/features/test_template_completeness.py`
- `PYTHONPATH=src python3 -m unittest tests/features/test_doctor.py`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli doctor --json`
- `sh tools/gauntlet.sh`
