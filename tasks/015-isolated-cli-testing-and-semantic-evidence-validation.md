---
type: Task Package
title: 'Task 015: Isolated CLI Testing & Semantic Evidence Validation'
description: 'Isolation af CLI-tests i midlertidige workspaces, bevarelse af ren git-status og semantisk validering i check-evidence'
status: stable
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-24T14:40:00Z'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-08-25T18:15:00Z'
tags:
- test-isolation
- evidence-validation
- ci
- hermetic
sources:
- id: code-review-20260823
  resource: docs/reviews/2026-08-23-architectural-code-review.md
  title: 'Architectural Code Review: agent-gauntlet (Findings CI-01, EVI-06, P0/P2)'
---

# Task 015: Isolated CLI Testing & Semantic Evidence Validation

**Status**: `DONE`  
**Intent**: `🐛 BUG FIX`  
**Oprettet**: `2026-08-24`  

## 🎯 Formål
Sikre fuldstændig hermetisk testafvikling og semantisk dybde i evidenskontrollen:
1. Isolere alle CLI-integrationstests i `tests/test_cli.py` i midlertidige, isolerede arbejdsområder (`tempfile.TemporaryDirectory`), så kørsel af unit tests aldrig muterer sporede filer (`evidence.json`, `evidence.md`, `tasks/*.md`) i rodmappen.
2. Opgradere `agent-gauntlet check-evidence` fra kun at tjekke kryptografisk signatur og træ-hash til også at validere semantiske invarianter (`status == 'PASSED'`, alle påkrævede tjek bestået, ingen uafklarede kriterier).
3. Tilføje `git diff --exit-code` i CI for at sikre at testsuiten efterlader arbejdsområdet 100% rent.

## 📋 Acceptance Criteria
- [x] Refakturere `tests/test_cli.py` så alle tests, der kalder `verify`, `init`, `tree-hash` eller `stamp`, kører i en isoleret `TemporaryDirectory`.
- [x] Verificere at kørsel af `python3 -m unittest discover tests` ikke ændrer eller snavser git status (`git status --porcelain` er tom).
- [x] Opgradere `check-evidence` i `src/agent_gauntlet/cli.py` til at afvise evidens med `status != 'PASSED'`, fejlede påkrævede tjek eller uafklarede acceptkriterier.
- [x] Tilføje `git diff --exit-code` i `.github/workflows/ci.yml` efter test- og gauntlet-kørsel.
- [x] Tilføje tests i `tests/test_cli.py` der bekræfter at `check-evidence` returnerer fejl (exit 1) på forfalskede, fejlede eller ufuldstændige evidensfiler.

## 🚫 Must NOT
- Må IKKE skrive test-artefakter eller erstatte sporede filer i repository-roden under testkørsel.
- Må IKKE godkende en evidensfil som `VALID` i `check-evidence`, hvis dens indhold repræsenterer en fejlet kørsel (`status: FAILED`).

## 📝 Revisions
- 2026-08-24: Oprettet som opfølgning på code review findings CI-01 (P0) og EVI-06 (P2).

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `git status --porcelain` (skal returnere tomt output efter testkørsel)
- `PYTHONPATH=src python3 -m agent_gauntlet.cli check-evidence`
