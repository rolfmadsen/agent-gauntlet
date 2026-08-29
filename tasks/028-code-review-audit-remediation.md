---
type: Task Package
title: 'Task 028: Two-Axis Code Review & Audit Remediation'
description: 'Udbedring af uafhængige audit-fund: Google docstrings overholdelse, eliminering af code smells, scaffolder AGENTS.md synkronisering og gatekeeper tilladte stier.'
status: draft
tags:
- task
- audit
- code-review
- docstrings
- gatekeeper
- scaffolding
- gauntlet
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-29T10:39:00Z'
---

# Task 028: Two-Axis Code Review & Audit Remediation

**Status**: `DONE`  
**Intent**: `🔄 REFACTOR`  
**Oprettet**: `2026-08-29`  
**Fuldført**: `2026-08-29`  

## 🎯 Formål
Udbedre samtlige fund identificeret under den uafhængige to-aksede granskning (`code-review`):
1. Berige offentlige API'er med fulde, strukturerede Google Docstrings (`Args:`, `Returns:`, `Raises:`) jf. `CODING_STANDARDS.md` Sektion 5.
2. Synkronisere `DEFAULT_AGENTS_MD` i `scaffolder.py` med `spec.md` governance og `🧐 CODE REVIEW / AUDIT` intent-klassifikation.
3. Tilføje `"coding_standards.md"` til `ALLOWED_METADATA_PATHS` i `gatekeeper.py` og eliminere ubrugte døde aliasser (`_resolve_task_contract`, `_is_active_task_content`).
4. Opdatere `spec.md` med `features/tasks/` i modulhierarkiet.

## 📋 Acceptance Criteria
- [x] Berige alle offentlige funktioner og klasser i `features/evidence/verifier.py`, `features/tasks/parser.py`, `features/scaffold/scaffolder.py`, `features/evidence/report.py` og `cli.py` med strukturerede Google Docstrings.
- [x] Tilføje `coding_standards.md` til `ALLOWED_METADATA_PATHS` i `src/agent_gauntlet/features/hooks/gatekeeper.py`.
- [x] Fjerne ubrugt død kode og ubrugte aliasser (`_resolve_task_contract` i `cli.py`, `_is_active_task_content` i `gatekeeper.py`).
- [x] Synkronisere `DEFAULT_AGENTS_MD` i `scaffolder.py` så den indeholder `## 📄 Specification Governance (spec.md)` og `🧐 CODE REVIEW / AUDIT`.
- [x] Opdatere `spec.md` så `features/tasks/` fremgår af feature-modulstrukturen.
- [x] Tilføje/opdatere tests i `tests/features/test_scaffold.py` og `tests/features/test_hooks.py` der verificerer de udbedrede forhold.
- [x] Alle 181+ enhedstests består, 46/46 mutanter i `tools/mutants.py` forbliver killed (100% kill-rate), og `agent-gauntlet okf validate` godkender alle filer.
- [x] `agent-gauntlet verify --task-id 028-code-review-audit-remediation --save` forsegler evidensen med status `PASSED`.

## 🚫 Must NOT
- Må IKKE bryde eksisterende offentlige funktionskald eller CLI-argumenter.
- Må IKKE introducere regressionsfejl i mutanter eller testsuiter.

## 📝 Revisions
- 2026-08-29: Oprettet på baggrund af fund fra to-akset code review audit.
- 2026-08-29: Udbedret samtlige fund: fuld Google docstrings dækning, renset døde aliasser, opdateret scaffolder skabelon, og 46/46 mutanter killed (100%).

## 🧪 Verifikation
- `PYTHONPATH="src:.venv/.venv/lib/python3.14/site-packages" python3 -m unittest discover tests`
- `PYTHONPATH="src:.venv/.venv/lib/python3.14/site-packages" python3 tools/mutants.py`
- `sh tools/gauntlet.sh`
- `PYTHONPATH="src:.venv/.venv/lib/python3.14/site-packages" python3 -m agent_gauntlet.cli verify --task-id 028-code-review-audit-remediation`
