---
type: Task Package
title: 'Task 031: Windsurf Cascade Adapter and Rules Bridge'
description: 'Implementation af Windsurf Cascade adapter, .windsurfrules og .windsurf/rules/ regelbro samt agent-gauntlet init --harness windsurf.'
status: draft
tags:
- task
- windsurf
- cascade
- harness
- adapter
- scaffolding
- gauntlet
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-29T10:50:00Z'
---

# Task 031: Windsurf Cascade Adapter and Rules Bridge

**Status**: `TODO`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-29`  

## 🎯 Formål
Etablere fuld understøttelse af Codeium's **Windsurf IDE** og **Cascade agent** i `agent-gauntlet` jf. [ROADMAP.md](ROADMAP.md) (Rangering 4):
1. Implementere autoritativ regelbro via `.windsurfrules` i rod-mappen samt modulære `.windsurf/rules/` filer, der instruerer Cascade i at læse og overholde `.agents/AGENTS.md` og TDD Task-kravene.
2. Udvide `agent-gauntlet init --harness windsurf` i `scaffolder.py` til deterministisk scaffolding af Windsurf-konfiguration.
3. Klargøre mapping af Cascade workflows og tool calls til gatekeeperens regler.

## 📋 Acceptance Criteria
- [ ] Oprette `src/agent_gauntlet/features/adapters/windsurf/` vertical slice modul med `WindsurfAdapter` og regel-skabeloner.
- [ ] Implementere scaffolding af `.windsurfrules` entrypoint-fil med autoritativ reference til `.agents/AGENTS.md`.
- [ ] Udvide `scaffolder.py` og CLI `--harness windsurf` flag.
- [ ] Tilføje sort-boks accepttests i `tests/features/test_adapter_windsurf.py` og `tests/test_cli.py`.
- [ ] Tilføje mutation testing i `tools/mutants.py` til at beskytte Windsurf-adapter logik (100% kill-rate).
- [ ] `agent-gauntlet okf validate` godkender alle oprettede og modificerede filer.

## 🚫 Must NOT
- Må IKKE duplikere `.agents/AGENTS.md` indhold; reglen skal fungere som en ren bro.
- Må IKKE overskrive eksisterende `.windsurfrules` uden `--force` flag.
- Må IKKE antage eksterne netværkskald.

## 📝 Revisions
- 2026-08-29: Oprettet som del af næste udviklingsepoke baseret på ROADMAP.md Rangering 4.

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `PYTHONPATH=src python3 tools/mutants.py`
- `sh tools/gauntlet.sh`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli init --harness windsurf`
