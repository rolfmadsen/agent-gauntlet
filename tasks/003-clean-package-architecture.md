---
type: Task Package
title: 'Task 003: Clean Package Architecture'
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

# Task 003: Package-by-Feature (Screaming Architecture) & Test-symmetri

**Status**: `DONE`  
**Intent**: `🔄 REFACTOR`  
**Oprettet**: `2026-08-22`  
**Fuldført**: `2026-08-22`  

## 🎯 Formål
Omlægge hele codebase og testsuite til en ren **Package-by-Feature** mappestruktur baseret på Uncle Bobs Clean Craftsmanship, fjerne midlertidige shims, og sikre 1:1 symmetri mellem `src/agent_gauntlet/features/` og `tests/features/`.

## 📋 Acceptance Criteria
- [x] Kildemapper organiseret som rene underpakker: `config/`, `diagnostics/`, `evidence/`, `gauntlet/`, `stacks/`.
- [x] Testmapper organiseret som rene underpakker i `tests/features/`.
- [x] Sletning af alle uaktuelle rod-filer og shims under `features/`.
- [x] Opdatering af `tools/mutants.py`, `tools/gauntlet.sh` og `plugin.json` (v0.2.0).
- [x] 100% test-pass (54/54) og 100% mutations-drab (18/18).

## 🚫 Must NOT
- Må IKKE introducere cykliske afhængigheder mellem feature-pakker.
- Må IKKE bryde eksisterende offentlige API-kontrakter.

## 🧪 Verifikation
- Gauntlet script: `sh tools/gauntlet.sh` (Alle 5 lag PASSED).
- Evidens: HMAC-SHA256 forseglet i `evidence.json`.
