---
type: Task Package
title: 'Task 004: Surgical Gatekeeper & Task Binding'
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

# Task 004: Kirurgisk Pre-Invocation Hook Gatekeeper & Task-Bound Evidens

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-22`  
**Fuldført**: `2026-08-22`  

## 🎯 Formål
Etablere en hård, ubrydelig Stop/Go gate og task-bundet evidensvalidering, som forhindrer AI-agenten i at redigere produktionskode i `src/` og `tests/` uden en aktiv, godkendt opgave i `tasks/`, samt sikre at `agent-gauntlet verify` forsegler den konkrete opgave og dens acceptkriterier under HMAC-signaturen.

## 📋 Acceptance Criteria
- [x] Implementere `src/agent_gauntlet/features/hooks/gatekeeper.py`, der blokerer redigering af `src/` og `tests/`, hvis der ikke findes en aktiv task i `tasks/`.
- [x] Gatekeeperen skal tillade alle læseværktøjer (`view_file`, `list_dir`, `grep_search`), scratch-filer, `tasks/`, `docs/` og `CONTEXT.md` uden forsinkelse.
- [x] Oprette `.agents/hooks.json` og opdatere `plugins/agent-gauntlet/plugin.json` med PreInvocation hook.
- [x] Udvide `EvidenceRecord` og `EvidenceAuthority` med `task_title`, `acceptance_criteria` og `unresolved_criteria`.
- [x] Implementere pre-flight validering i `agent-gauntlet verify`, der tjekker `CONTEXT.md`, opgaver i `tasks/` og at alle acceptkriterier er afkrydset (`- [x]`).
- [x] Tilføje `--standalone` flag til `verify` for scratch/ad-hoc kørsel.
- [x] Skrive sort-boks tests i `tests/features/test_hooks.py` og opdatere `test_evidence.py` samt `test_cli.py`.
- [x] 100% test-pass og 100% dræbte mutanter i `tools/mutants.py`.

## 🚫 Must NOT
- Må IKKE blokere læseoperationer som view_file eller list_dir.
- Må IKKE tillade skriveadgang til beskyttede mapper uden en aktiv opgave.

## 🧪 Verifikation
- Unit & Acceptance: `PYTHONPATH=src python3 -m unittest discover tests` (63 tests bestået)
- Gauntlet script: `sh tools/gauntlet.sh` (5/5 lag bestået, 21/21 mutanter dræbt)
- Evidence check: `PYTHONPATH=src python3 -m agent_gauntlet.cli check-evidence` ([VALID])
