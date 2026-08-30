---
type: Task Package
title: 'Task 039: Early-Phase Specification and Business Rules Gatekeeper'
description: 'Implementering af tidlig-fase krav- og forretningsregel-gatekeeper (agent-gauntlet check-spec og Gatekeeper Hook), der mekanisk håndhæver at forretningsregler (Must NOT), acceptkriterier og domænebegreber i CONTEXT.md er afklaret før kodning.'
status: stable
tags:
- task
- governance
- spec
- business-rules
- context
- gatekeeper
- shift-left
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-30T09:54:00Z'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-08-30T10:00:00Z'
---

# Task 039: Early-Phase Specification and Business Rules Gatekeeper

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-30`  
**Fuldført**: `2026-08-30`  

## 🎯 Formål
Etablere en mekanisk **Shift-Left Gatekeeper** (`agent-gauntlet check-spec`), der forhindrer AI-agenter i at skrive produktionskode i blinde uden forudgående afklaring af domænebegreber og forretningsregler:
1. **Tvungen Forretningsregel-Deklaration (`Must NOT`)**: Sikre at enhver aktiv opgave (`tasks/0xx-*.md`) og `spec.md` indeholder eksplicitte negative begrænsninger og forretningsinvarianter.
2. **Begrebs- og Ordbogs-Validering (`CONTEXT.md`)**: Verificere at `CONTEXT.md` overholder Aristoteles-formatet (*genus et differentiam* med `_Avoid_:` linjer), og at alle nøglebegreber i opgavebeskrivelser er defineret i glossariet.
3. **Mekanisk Skrive-Spærring i Gatekeeper Hooks (`gatekeeper.py`)**: Fysisk blokere oprettelse eller redigering af filer i `src/` og `tests/`, hvis der ikke foreligger en formelt godkendt og valideret opgave (`is_task_active` kræver bestået spec-validering).
4. **Actionable Socratic Diagnostics**: Give præcise remediation hints og sokratiske spørgsmål til agenten, hvis en opgave mangler forretningsregler eller bruger udefinerede begreber.

## 📋 Acceptance Criteria
- [x] **Kerne Spec & Business Rules Validator (`features/tasks/spec_gate.py`)**:
  - [x] Implementere `check_task_specification(task_path: Path, workspace: Path) -> SpecReadinessReport`.
  - [x] Validere at opgavefilen indeholder:
    - [x] Gyldigt OKF v0.2 frontmatter med `type: Task Package`.
    - [x] Ikke-tom `## 🚫 Must NOT` sektion med mindst én konkret negativ invariant/forretningsregel.
    - [x] `## 📋 Acceptance Criteria` med mindst ét eksekverbart `- [ ]` punkt.
    - [x] `## 🎯 Formål` med klar afgrænsning.
  - [x] Implementere `validate_context_glossary(workspace: Path) -> list[DiagnosticFinding]`:
    - [x] Verificere at alle begreber i `CONTEXT.md` følger formlen `**Term**:\n<Definition>\n_Avoid_: <synonymer>`.
    - [x] Advare hvis markerede domænebegreber i `tasks/*.md` mangler i `CONTEXT.md`.
- [x] **CLI Integration (`agent-gauntlet check-spec`)**:
  - [x] Tilføje `check-spec` subcommand til CLI parseren i `src/agent_gauntlet/cli.py`.
  - [x] Understøtte flag: `--task <id|path>`, `--all`, `--workspace`, `--json`.
  - [x] Returnere exit code `0` ved godkendt specifikation og `1` ved manglende forretningsregler/begreber med strukturerede diagnostiske hints.
- [x] **Gatekeeper Hook Integration (`features/hooks/gatekeeper.py`)**:
  - [x] Opdatere `is_task_active(content)` og `PolicyEngine.evaluate(request, context)` til at kræve eksplicitte `Must NOT` invarianter og godkendt status før skriveadgang til `src/` og `tests/`.
- [x] **FSM & Session Handoff Integration**:
  - [x] Opdatere `infer_next_session_role()` i `verifier.py` til at instruere `System Architecture & Requirements`-rollen i at køre `agent-gauntlet check-spec`.
- [x] **Gauntlet & Mutation Testing**:
  - [x] Tilføje unit- og acceptance-tests i `tests/features/test_check_spec.py`.
  - [x] Tilføje syntetiske mutanter i `tools/mutants.py` og opnå 100% kill-rate.
  - [x] `agent-gauntlet okf validate` godkender alle metadata-filer.

## 🚫 Must NOT
- Må IKKE tillade en task med tom eller manglende `Must NOT` sektion at have status `ACTIVE`.
- Må IKKE tillade skriveadgang til `src/` eller `tests/`, hvis opgaven er i `status: draft` eller mangler forretningsinvarianter.
- Må IKKE overskrive eller ændre `tasks/*.md` eller `CONTEXT.md` automatisk (skal være read-only validering med rådgivende hints).

## 📝 Revisions
- 2026-08-30: Oprettet som Shift-Left forretningsregel- og begrebs-gatekeeper efter afdækning af procesgab i tidlige faser.
- 2026-08-30: Færdiggjort, testet og verificeret med 59/59 mutanter dræbt.

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m agent_gauntlet.cli check-spec`
- `PYTHONPATH=src python3 -m unittest tests/features/test_check_spec.py`
- `sh tools/gauntlet.sh`
