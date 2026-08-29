---
type: Task Package
title: 'Task 032: GitHub Copilot and OpenAI Codex Instruction Bridge'
description: 'Implementation af GitHub Copilot instruktionsbro (.github/copilot-instructions.md) samt agent-gauntlet init --harness copilot.'
status: draft
tags:
- task
- copilot
- codex
- harness
- adapter
- scaffolding
- gauntlet
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-29T10:50:00Z'
---

# Task 032: GitHub Copilot and OpenAI Codex Instruction Bridge

**Status**: `TODO`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-29`  

## 🎯 Formål
Etablere understøttelse af **GitHub Copilot** (og OpenAI Codex/Assistant interfaces) i `agent-gauntlet` jf. [ROADMAP.md](ROADMAP.md) (Rangering 5):
1. Implementere autoritativ instruktionsbro via `.github/copilot-instructions.md`, der instruerer Copilot Chat / Workspace i at overholde projektets TDD-disciplin, Task-krav og forbyder kildekode-ændringer uden en aktiv task i `tasks/`.
2. Udvide `agent-gauntlet init --harness copilot` og `--harness codex` i `scaffolder.py`.
3. Sikre at Copilot-instruktionerne har korrekt syntaks og autoritative referencer til `.agents/AGENTS.md` og `CODING_STANDARDS.md`.

## 📋 Acceptance Criteria
- [ ] Oprette `src/agent_gauntlet/features/adapters/copilot/` vertical slice modul med `CopilotAdapter` og instruktionsskabeloner.
- [ ] Implementere scaffolding af `.github/copilot-instructions.md` med autoritativ reference til `.agents/AGENTS.md`.
- [ ] Udvide `scaffolder.py` og CLI `--harness copilot` og `--harness codex` flag.
- [ ] Tilføje sort-boks accepttests i `tests/features/test_adapter_copilot.py` og `tests/test_cli.py`.
- [ ] Tilføje mutation testing i `tools/mutants.py` til at beskytte Copilot-adapter logik (100% kill-rate).
- [ ] `agent-gauntlet okf validate` godkender alle oprettede og modificerede filer.

## 🚫 Must NOT
- Må IKKE overskrive eksisterende `.github/copilot-instructions.md` uden `--force` flag.
- Må IKKE introducere eksterne afhængigheder eller netværkskald.

## 📝 Revisions
- 2026-08-29: Oprettet som del af næste udviklingsepoke baseret på ROADMAP.md Rangering 5.

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `PYTHONPATH=src python3 tools/mutants.py`
- `sh tools/gauntlet.sh`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli init --harness copilot`
