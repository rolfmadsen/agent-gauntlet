---
type: Task Package
title: 'Task 030: Cursor IDE Adapter and Rules Bridge'
description: 'Implementation af dedikeret Cursor IDE adapter, .cursor/rules/agent-gauntlet.mdc regelbro og agent-gauntlet init --harness cursor understøttelse.'
status: draft
tags:
- task
- cursor
- harness
- adapter
- scaffolding
- gauntlet
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-29T10:50:00Z'
---

# Task 030: Cursor IDE Adapter and Rules Bridge

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-29`  

## 🎯 Formål
Etablere fuld understøttelse af **Cursor IDE** i `agent-gauntlet` via vertical slice adapter-arkitekturen jf. [ADR 0001](docs/adr/0001-package-by-feature-architecture.md) og [ROADMAP.md](ROADMAP.md) (Rangering 3):
1. Implementere autoritativ regelbro via `.cursor/rules/agent-gauntlet.mdc` med YAML frontmatter (`alwaysApply: true`), der instruerer Cursor AI i at overholde `.agents/AGENTS.md` og `CODING_STANDARDS.md`.
2. Tilføje valgfri legacy fallback `.cursorrules` i projektets rod.
3. Udvide `agent-gauntlet init --harness cursor` i `scaffolder.py` til automatisk at konfigurere Cursor-regler og instruktioner.
4. Tilføje Cursor tool-aliasing i adapter-laget hvis relevant.

## 📋 Acceptance Criteria
- [x] Oprette `src/agent_gauntlet/features/adapters/cursor/` vertical slice modul med `CursorAdapter` og regel-skabeloner.
- [x] Implementere scaffolding af `.cursor/rules/agent-gauntlet.mdc` med `description`, `globs: "*"` og `alwaysApply: true`, der peger autoritativt på `.agents/AGENTS.md`.
- [x] Udvide `scaffolder.py` og CLI `--harness cursor` flag til at generere Cursor konfiguration deterministisk.
- [x] Tilføje sort-boks accepttests i `tests/features/test_adapter_cursor.py` og `tests/test_cli.py`.
- [x] Tilføje mutation testing i `tools/mutants.py` til at beskytte Cursor-adapter logik (100% kill-rate).
- [x] `agent-gauntlet okf validate` godkender alle oprettede og modificerede filer.

## 🚫 Must NOT
- Må IKKE duplikere regelindhold fra `.agents/AGENTS.md` ind i `.cursor/rules/`; reglen skal fungere som en autoritativ bro (single source of truth).
- Må IKKE overskrive eksisterende brugerdefinerede `.cursor/rules/` uden eksplicit `--force` flag.
- Må IKKE introducere eksterne afhængigheder.

## 📝 Revisions
- 2026-08-29: Oprettet som del af næste udviklingsepoke baseret på ROADMAP.md Rangering 3.
- 2026-08-29: Implementeret CursorAdapter, CursorRulesValidator, scaffolding support via `--harness cursor`, sort-boks tests og mutation testing (100% kill-rate).

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `PYTHONPATH=src python3 tools/mutants.py`
- `sh tools/gauntlet.sh`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli init --harness cursor`
