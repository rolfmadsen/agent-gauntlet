---
type: Task Package
title: 'Task 008: Session Handoff Prompt Generator'
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
- by: process:agent-gauntlet-verify
  at: '2026-08-23T13:51:21Z'
- by: process:agent-gauntlet-verify
  at: '2026-08-23T13:51:35Z'
---

# Task 008: Session Handoff Prompt Generator

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-23`  
**Fuldført**: `2026-08-23`  

## 🎯 Formål
Implementere en mekanisk Session Handoff Prompt Generator i `agent-gauntlet verify` og CLI-udskriften, som automatisk genererer en copy-paste klar opstartsprompt til en ny chat-session, når en opgave fuldføres og forsegles med grøn evidens.

## 📋 Acceptance Criteria
- [x] Implementere en funktion i `src/agent_gauntlet/cli.py` (eller tilknyttet modul), der genererer en deterministisk session handoff starter-prompt ved grøn verifikation.
- [x] Ved kørsel af `agent-gauntlet verify`, når verifikationen er `PASSED` for en navngiven opgave, udskrives en tydelig Session Handoff boks med den færdige copy-paste prompt til brugeren.
- [x] Ved kørsel med `--diagnostics-json` inkluderes `handoff_prompt` som et felt i JSON-outputtet.
- [x] Sort-boks accepttests i `tests/test_cli.py` validerer at handoff-prompten udskrives ved bestået verifikation.
- [x] 100% mutation kill-rate opretholdes i `tools/mutants.py`.

## 🚫 Must NOT
- Må IKKE udskrive en handoff-prompt hvis verifikationen fejler (`FAILED`).
- Må IKKE overskrive eksisterende CLI-flag eller ødelægge JSON-output formater.

## 📝 Revisions
- 2026-08-23: Oprettet efter brugeranmodning om en synlig, mekanisk copy-paste handoff blok ved opgaveafslutning.

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `PYTHONPATH=src python3 tools/mutants.py`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli verify --task-id 008-session-handoff-prompt-generator`
