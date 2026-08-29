---
type: Task Package
title: 'Task 024: Role-Aware Session Handoff Engine'
status: stable
tags:
- task
- gauntlet
- handoff
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-29T09:35:00Z'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-08-29T09:40:57Z'
---

# Task 024: Role-Aware Session Handoff Engine

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-29`  
**Fuldført**: `2026-08-29`  

## 🎯 Formål
Implementere en deterministisk, branchespecifik og rolle-bevidst Session Handoff motor i `agent-gauntlet`, der udregner den rette ingeniørrolle (f.eks. *System Architecture & Requirements*, *Feature Implementation & Testing*, *Independent Code Review & Audit*) og genererer en målrettet starter-prompt baseret på opgavens tilstand (`DRAFT` vs `ACTIVE` vs `DONE`).

Funktionaliteten forankres direkte i kernen (`verifier.py`), CLI-udskriften (`cli.py`) og scaffolderen (`scaffolder.py`), så den fungerer universelt på tværs af alle eksisterende og ny-initierede projekter.

## 📋 Acceptance Criteria
- [x] Implementere `infer_next_session_role(workspace: Path, current_task_id: str) -> tuple[str, str, str]` i `src/agent_gauntlet/features/evidence/verifier.py`, der returnerer `(next_role, next_task_id, handoff_prompt)`.
- [x] For `DRAFT` opgaver eller opgaver uden acceptkriterier returneres rollen `Senior Software Engineer (System Architecture & Requirements)` med fokus på specifikation, invariants og `spec.md`.
- [x] For `ACTIVE` opgaver med udestående kriterier returneres rollen `Senior Software Engineer (Feature Implementation & Testing)` med fokus på TDD-disciplin og `spec.md`.
- [x] Når alle opgaver er `DONE` (eller ingen opgaver findes), returneres rollen `Senior Software Engineer (Independent Code Review & Audit)` med fokus på uafhængig granskning.
- [x] Opdatere `execute_verify()` og CLI-outputtet til at udskrive `Næste Rolle` i det visuelle Session Handoff kort.
- [x] Inkludere `next_role` og `handoff_prompt` som dedikerede felter i `--diagnostics-json` outputtet.
- [x] Opdatere `DEFAULT_AGENTS_MD` i `scaffolder.py` og `.agents/AGENTS.md` med det opdaterede Handoff Card template (`**Næste Rolle**: ...`).
- [x] Sort-boks enhedstests i `tests/features/test_evidence.py`, `tests/features/test_scaffold.py` og `tests/test_cli.py` verificerer al ny adfærd.
- [x] 100% test pass og 100% mutation kill-rate opretholdes i `tools/mutants.py`.

## 🚫 Must NOT
- Må IKKE hardcode interne eller private skill-navne (som `old-coder`) i de genererede prompts.
- Må IKKE udskrive en handoff-prompt hvis verifikationen fejler (`FAILED`).
- Må IKKE bryde eksisterende JSON-felter eller CLI-kontrakter.

## 📝 Revisions
- 2026-08-29: Oprettet efter brugergodkendelse af implementeringsplanen for rolle-bevidste faseskift.
- 2026-08-29: Fuldført med 180 passerede enhedstests og 46/46 mutanter killed (100%).

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `PYTHONPATH=src python3 tools/mutants.py`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli verify --task-id 024-role-aware-session-handoffs`
