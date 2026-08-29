---
type: Task Package
title: 'Task 029: Audit-Aware Release Handoff Finite State Machine'
description: 'Udvidelse af infer_next_session_role() med en komplet livscyklus-tilstandsmaskine: overgang fra Code Review & Audit til Release & Operations Engineer ved godkendt audit.'
status: draft
tags:
- task
- handoff
- fsm
- release
- code-review
- gauntlet
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-29T10:48:00Z'
---

# Task 029: Audit-Aware Release Handoff Finite State Machine

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-29`  
**Fuldført**: `2026-08-29`  

## 🎯 Formål
Forhindre uendelige code-review løkker (*review fatigue* / *bikeshedding*) ved at implementere en deterministisk livscyklus-tilstandsmaskine i `infer_next_session_role()`:
1. Når feature-opgaver afsluttes for første gang, peger handoff på `Senior Software Engineer (Independent Code Review & Audit)`.
2. Når et code review / audit er gennemført og godkendt (eller seneste opgave er en audit/review task, der er `DONE`), overgår systemet deterministisk til `Release & Operations Engineer (Release Attestation & Deployment)`.
3. Give klare, handlingsorienterede starter-prompts for release-attestering, deployment og overgang til næste epoke i `ROADMAP.md`.

## 📋 Acceptance Criteria
- [x] Implementere `is_audit_or_review_task(task_id: str, title: str = "", content: str = "") -> bool` hjælperfunktion til at identificere audit- og review-opgaver.
- [x] Opdatere `infer_next_session_role()` i `src/agent_gauntlet/features/evidence/verifier.py`:
  - Hvis alle opgaver er `DONE` og den seneste/aktuelle opgave var et code review/audit $\to$ Returner `Release & Operations Engineer (Release Attestation & Deployment)` med release starter-prompt.
  - Hvis alle opgaver er `DONE`, men ingen audit/review opgave er gennemført $\to$ Returner `Senior Software Engineer (Independent Code Review & Audit)`.
- [x] Tilføje sort-boks accepttests i `tests/features/test_evidence.py` og `tests/test_cli.py`, der verificerer:
  - Overgang til `Independent Code Review & Audit` efter almindelige feature-opgaver.
  - Overgang til `Release & Operations Engineer` efter fuldført audit/review opgave.
- [x] Alle 181+ enhedstests består, 46/46 mutanter i `tools/mutants.py` forbliver killed (100% kill-rate), og `agent-gauntlet okf validate` godkender alle filer.
- [x] `agent-gauntlet verify --task-id 029-audit-aware-release-handoff-fsm --save` forsegler evidensen med status `PASSED`.

## 🚫 Must NOT
- Må IKKE bryde eksisterende API-signatur for `infer_next_session_role(workspace: Path, current_task_id: str = "") -> tuple[str, str, str]`.
- Må IKKE antage eksterne netværkskald eller introducere ikke-deterministisk adfærd.

## 📝 Revisions
- 2026-08-29: Oprettet for at løse problemet med uendelige AI code review loops og sikre en deterministisk stop-tilstand mod Release.
- 2026-08-29: Implementeret audit-detektion og overgang til Release & Operations Engineer i infer_next_session_role(), 183 tests bestået, 46/46 mutanter killed.

## 🧪 Verifikation
- `PYTHONPATH="src:.venv/.venv/lib/python3.14/site-packages" python3 -m unittest discover tests`
- `PYTHONPATH="src:.venv/.venv/lib/python3.14/site-packages" python3 tools/mutants.py`
- `sh tools/gauntlet.sh`
- `PYTHONPATH="src:.venv/.venv/lib/python3.14/site-packages" python3 -m agent_gauntlet.cli verify --task-id 029-audit-aware-release-handoff-fsm`
