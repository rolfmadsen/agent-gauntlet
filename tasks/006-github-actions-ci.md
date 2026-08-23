---
type: Task Package
title: 'Task 006: GitHub Actions CI'
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

# Task 006: GitHub Actions Continuous Integration (CI) Workflow

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-22`  
**Fuldført**: `2026-08-22`  

## 🎯 Formål
Etablere en robust GitHub Actions workflow (`.github/workflows/ci.yml`), der automatisk bygger, tester og validerer `agent-gauntlet` på rene Ubuntu-runners på tværs af understøttede Python-versioner (3.10, 3.11, 3.12) ved hvert push og pull request for at garantere miljøuafhængighed og fravær af lokale afhængigheder.

## 📋 Acceptance Criteria
- [x] Oprette `.github/workflows/ci.yml` med triggers på `push` og `pull_request`.
- [x] Konfigurere test-matrix for Python `3.10`, `3.11` og `3.12` på `ubuntu-latest`.
- [x] Installere pakken i editable tilstand (`pip install -e .`).
- [x] Køre komplet test-suite (`python -m unittest discover tests`).
- [x] Køre mutation gauntlet (`python tools/mutants.py`).
- [x] Køre fuld 5-lags gauntlet (`sh tools/gauntlet.sh`).
- [x] Validere kryptografisk evidens og drift-kontrol (`agent-gauntlet check-evidence`).
- [x] Opdatere `tasks/006-github-actions-ci.md` til `Status: DONE` og forsegle `evidence.json`.

## 🚫 Must NOT
- Må IKKE fejle på grund af manglende hemmeligheder eller eksterne netværkskald.
- Må IKKE udføre automatiske git pushes eller release-publiceringer uden menneskelig godkendelse.

## 📝 Revisions
- 2026-08-22: Oprettet og implementeret efter brugeranmodning om automatisk CI-test i skyen for at validere miljøuafhængighed på tværs af Python 3.10-3.12.

## 🧪 Verifikation
- Lokal gauntlet: `sh tools/gauntlet.sh` (100% pass rate, 23/23 mutanter dræbt).
- Evidens-forsegling: `agent-gauntlet verify --task-id 006-github-actions-ci`.
