---
type: Task Package
title: 'Task 007: Claude Bridge & Scaffolding'
status: stable
tags:
- task
- gauntlet
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-23T11:00:00Z'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-08-23T11:30:00Z'
---

# Task 007: Claude Code Bridge & Multi-Harness Scaffolding

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-23`  
**Fuldført**: `2026-08-23`  

## 🎯 Formål
Etablere en officiel Claude Code bridge i `agent-gauntlet` ved at:
1. Gøre `CLAUDE.md` til en autoritativ reference mod `.agents/AGENTS.md`.
2. Tillade redigering af `CLAUDE.md`, `ROADMAP.md` og `spec.md` som tilladte metadata-filer i gatekeeperen (`ALLOWED_METADATA_PATHS`).
3. Opdatere `scaffolder.py` så `CLAUDE.md` automatisk oprettes som standard ved `agent-gauntlet init`.
4. Opdatere tests i `tests/features/test_scaffold.py` og `tests/features/test_hooks.py`.

## 📋 Acceptance Criteria
- [x] `CLAUDE.md` findes i roden af `agent-gauntlet` og peger autoritativt på `.agents/AGENTS.md`.
- [x] `gatekeeper.py` tillader `CLAUDE.md`, `ROADMAP.md` og `spec.md` i `ALLOWED_METADATA_PATHS` uden krav om forudgående aktiv task.
- [x] `scaffolder.py` inkluderer `CLAUDE.md` i standard scaffolding-listen under `agent-gauntlet init`.
- [x] Sort-boks enhedstests i `tests/features/test_scaffold.py` og `tests/features/test_hooks.py` dækker de nye tilføjelser.
- [x] Alle enhedstests og 100% mutation testing passerer.

## 🚫 Must NOT
- Må IKKE overskrive en eksisterende `CLAUDE.md` ved `init`, medmindre `--force` er angivet.
- Må IKKE introducere afhængigheder til specifikke LLM API-biblioteker.

## 📝 Revisions
- 2026-08-23: Oprettet efter brugeranmodning om multi-harness bridge for Claude Code.

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `PYTHONPATH=src python3 tools/mutants.py`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli verify`
