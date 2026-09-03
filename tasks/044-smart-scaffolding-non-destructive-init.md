---
type: Task Package
title: 'Task 044: Context-Aware Smart Scaffolding and Non-Destructive Init'
description: 'Forhindre skabelon-forurening ved kørsel af agent-gauntlet init i eksisterende projekter: spring 001-bootstrap.md og 0001-initial-architecture.md over hvis tasks og ADRs allerede findes.'
status: stable
tags:
- task
- scaffold
- init
- non-destructive
- craftsmanship
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-09-03T19:15:00Z'
---

# Task 044: Context-Aware Smart Scaffolding and Non-Destructive Init

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-09-03`  

## 🎯 Formål
Forhindre utilsigtet skabelon-forurening, når `agent-gauntlet init` eller `scaffold` afvikles i et eksisterende, modent repository:
1. **Kontekst-bevidst Task Scaffolding**: Hvis `tasks/` allerede indeholder opgaver (f.eks. `tasks/043-...`), skal den **ikke** oprette en overflødig `001-bootstrap.md`, men markere den som `SKIPPED`.
2. **Kontekst-bevidst ADR Scaffolding**: Hvis `docs/adr/` allerede indeholder arkitekturbeslutninger, skal den **ikke** oprette en overflødig `0001-initial-architecture.md`, men markere den som `SKIPPED`.
3. **Opdatering af rod CODING_STANDARDS.md**: Bring repositoryets egen `CODING_STANDARDS.md` i overensstemmelse med de detekterede polyglot-stakke (Python + TypeScript + Rust).

## 📋 Acceptance Criteria
- [x] **Smart Task Scaffolding i `ProjectScaffolder`**:
  - [x] Hvis `workspace / "tasks"` indeholder mindst én `.md`-fil, oprettes `tasks/001-bootstrap.md` IKKE, men registreres som `ScaffoldStatus.SKIPPED`.
  - [x] Hvis `tasks/` er tom eller ikke findes, oprettes `tasks/001-bootstrap.md` normalt som `ScaffoldStatus.CREATED`.
- [x] **Smart ADR Scaffolding i `ProjectScaffolder`**:
  - [x] Hvis `workspace / "docs/adr"` indeholder mindst én anden markdown-fil end `README.md`, oprettes `docs/adr/0001-initial-architecture.md` IKKE, men registreres som `ScaffoldStatus.SKIPPED`.
  - [x] Hvis `docs/adr/` kun indeholder `README.md` eller er tom, oprettes `docs/adr/0001-initial-architecture.md` normalt.
- [x] **Dobbelt-Træ Konsistens**:
  - [x] Ændringerne i `scaffolder.py` synkroniseres til både `src/agent_gauntlet/` og `packages/agent-gauntlet/src/`.
- [x] **Enhedstest i `tests/features/test_scaffold.py`**:
  - [x] Tilføj test der beviser, at eksisterende tasks blokerer for dannelsen af `001-bootstrap.md`.
  - [x] Tilføj test der beviser, at eksisterende ADRs blokerer for dannelsen af `0001-initial-architecture.md`.
- [x] **Opdatering af repositoryets `CODING_STANDARDS.md`**:
  - [x] Opdater `CODING_STANDARDS.md` til fulde polyglot standarder via generatoren (`Python + TypeScript + Rust`).
- [x] **Gauntlet Verifikation**:
  - [x] Alle 7 lag i `tools/gauntlet.sh` passerer 100% (65/65 mutanter dræbt).

## 🚫 Must NOT
- Må IKKE bryde eksisterende scaffolding af helt tomme/nye workspaces (i tomme mapper skal `001-bootstrap.md` og `0001-initial-architecture.md` stadig dannes).
- Må IKKE overskrive eksisterende filer uden `--force`.
- Må IKKE fejle hvis `tasks/` eller `docs/adr/` slet ikke eksisterer ved start.

## 📝 Revisions
- 2026-09-03: Oprettet efter bruger-observation af, at `init` i modne projekter forurenede mapper med `001-bootstrap.md` og `0001-initial-architecture.md`.

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `sh tools/gauntlet.sh`
