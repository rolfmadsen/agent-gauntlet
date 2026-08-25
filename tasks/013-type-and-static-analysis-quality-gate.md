---
type: Task Package
title: 'Task 013: Type & Static Analysis Quality Gate (Pyright & Ruff Integration)'
description: Udryddelse af alle 20 Pyright-fejl, Ruff-tilpasning og integration af
  obligatorisk type- og lint-tjek i gauntlet og CI
status: stable
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-24T14:40:00Z'
tags:
- pyright
- ruff
- typing
- quality-gate
- ci
sources:
- id: code-review-20260823
  resource: docs/reviews/2026-08-23-architectural-code-review.md
  title: 'Architectural Code Review: agent-gauntlet (Findings CI-02, P1)'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-08-25T15:27:32Z'
- by: process:agent-gauntlet-verify
  at: '2026-08-25T15:27:32Z'
- by: process:agent-gauntlet-verify
  at: '2026-08-25T15:27:38Z'
- by: process:agent-gauntlet-verify
  at: '2026-08-25T15:27:38Z'
---

# Task 013: Type & Static Analysis Quality Gate (Pyright & Ruff Integration)

**Status**: `DONE`  
**Intent**: `🐛 BUG FIX`  
**Oprettet**: `2026-08-24`  

## 🎯 Formål
Gøre typesikkerhed og statisk analyse til et reelt, håndhævet kvalitetsgitter i `agent-gauntlet`:
1. Rette samtlige 20 Pyright type-fejl i `src/agent_gauntlet/` og `tests/` (herunder return type i `cli.py`, null-checks i `validator.py`, `loader.py`, `profiles.py` og `test_okf.py`).
2. Tilføje `ruff` og `pyright` som obligatoriske matricetrin i `.github/workflows/ci.yml` og lag i `tools/gauntlet.sh`.
3. Opdatere `pyproject.toml` med pinning af udviklings- og typecheck-afhængigheder.

## 📋 Acceptance Criteria
- [x] Rette typefejl i `src/agent_gauntlet/cli.py` (`_ExitCode` vs `int`, `record.signature` optional subscript).
- [x] Rette typefejl i `src/agent_gauntlet/features/config/loader.py` (`yaml.load` safe handling ved manglende modul).
- [x] Rette typefejl i `src/agent_gauntlet/features/okf/validator.py` (håndtering af `None` i dato-sammenligninger og metadata-adgang).
- [x] Rette typefejl i `src/agent_gauntlet/features/stacks/profiles.py` (`TypeIs` annotering).
- [x] Rette typefejl i `tests/features/test_okf.py` (sikre null-guards før opslag i `doc.metadata`).
- [x] Verificere at `pyright` rapporterer 0 errors og 0 warnings på tværs af hele kodebasen (`src`, `tests`, `tools`).
- [x] Tilføje `ruff check .` og `pyright` i `tools/gauntlet.sh`.
- [x] Opdatere `.github/workflows/ci.yml` til at installere og køre linting og typecheck som obligatoriske trin.

## 🚫 Must NOT
- Må IKKE anvende `# type: ignore` eller `Any` som symptombehandling på steder, hvor korrekte typespecifikationer og null-guards er mulige.
- Må IKKE gøre lint og typecheck valgfrie i standard Python gauntlet profilen.

## 📝 Revisions
- 2026-08-24: Oprettet som opfølgning på code review finding CI-02 (P1) for at etablere et rent typegitter.

## 🧪 Verifikation
- `pyright src tests tools`
- `ruff check .`
- `sh tools/gauntlet.sh`
