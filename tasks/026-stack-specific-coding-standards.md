---
type: Task Package
title: 'Task 026: Stack-Specific Coding Standards Generation'
description: 'Automatisk generering af autoritative coding standards (Google Python, Google TypeScript/React, Rust API Guidelines) i agent-gauntlet scaffolding.'
status: draft
tags:
- task
- scaffolding
- coding-standards
- google-styleguide
- rust-api-guidelines
- gauntlet
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-29T10:11:00Z'
---

# Task 026: Stack-Specific Coding Standards Generation

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-29`  
**Fuldført**: `2026-08-29`  

## 🎯 Formål
Tilføje autoritativ, stack-specifik generering af `CODING_STANDARDS.md` til `ProjectScaffolder` i `agent-gauntlet`, så ethvert nyt eller initialiseret projekt automatisk forsynes med klare, industrianerkendte standarder tilpasset den valgte tech stack:
1. **Python**: Google Python Style Guide + PEP 8 / PEP 484.
2. **TypeScript / React**: Google TypeScript Style Guide + moderne funktionelle React/Hooks principper.
3. **Rust**: Official Rust API Guidelines (Naming, Error handling, Newtype, Borrowing).

## 📋 Acceptance Criteria
- [x] Definere `CODING_STANDARDS_PYTHON` skabelon i `src/agent_gauntlet/features/scaffold/scaffolder.py` baseret på Google Python Style Guide.
- [x] Definere `CODING_STANDARDS_TYPESCRIPT` skabelon i `src/agent_gauntlet/features/scaffold/scaffolder.py` baseret på Google TypeScript Style Guide og React retningslinjer.
- [x] Definere `CODING_STANDARDS_RUST` skabelon i `src/agent_gauntlet/features/scaffold/scaffolder.py` baseret på Official Rust API Guidelines.
- [x] Opdatere `ProjectScaffolder.scaffold()` til automatisk at generere `CODING_STANDARDS.md` i rodmappen afhængigt af den valgte `stack` parameter.
- [x] Oprette `CODING_STANDARDS.md` i rodmappen for `agent-gauntlet` baseret på Python standarden.
- [x] Tilføje sort-boks accepttests i `tests/features/test_scaffold.py`, der verificerer generering af `CODING_STANDARDS.md` for hhv. `python`, `typescript` og `rust`.
- [x] Alle 181 enhedstests passerer, og 46/46 mutanter i `tools/mutants.py` forbliver killed (100% kill-rate).
- [x] `agent-gauntlet verify --task-id 026-stack-specific-coding-standards --save` forsegler evidensen med status `PASSED`.

## 🚫 Must NOT
- Må IKKE overskrive eksisterende `CODING_STANDARDS.md` medmindre `--force` er angivet.
- Må IKKE indeholde modstridende eller forældede regler i de genererede skabeloner.
- Må IKKE bryde eksisterende scaffolding- eller verifikations-invarianter.

## 📝 Revisions
- 2026-08-29: Oprettet efter brugergodkendelse af implementeringsplanen for stack-specifikke coding standards.
- 2026-08-29: Fuldført med 181 enhedstests og 46/46 mutanter killed (100%).

## 🧪 Verifikation
- `PYTHONPATH="src:.venv/.venv/lib/python3.14/site-packages" python3 -m unittest discover tests`
- `PYTHONPATH="src:.venv/.venv/lib/python3.14/site-packages" python3 tools/mutants.py`
- `sh tools/gauntlet.sh`
- `PYTHONPATH="src:.venv/.venv/lib/python3.14/site-packages" python3 -m agent_gauntlet.cli verify --task-id 026-stack-specific-coding-standards`
