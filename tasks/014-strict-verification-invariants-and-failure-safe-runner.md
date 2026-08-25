---
type: Task Package
title: 'Task 014: Strict Verification Invariants & Failure-Safe Gauntlet Semantics'
description: 'Gør PASSED til en strikt domæne-invariant, eliminér slugning af exit 127 fejl og forhindr partiel test-attestering'
status: stable
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-24T14:40:00Z'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-08-25T16:09:15Z'
tags:
- gauntlet
- verification
- invariants
- evidence
- runner
- okf
sources:
- id: code-review-20260823
  resource: docs/reviews/2026-08-23-architectural-code-review.md
  title: 'Architectural Code Review: agent-gauntlet (Findings EVI-02, EVI-03, P0)'
---

# Task 014: Strict Verification Invariants & Failure-Safe Gauntlet Semantics

**Status**: `DONE`  
**Intent**: `🐛 BUG FIX`  
**Oprettet**: `2026-08-24`  

## 🎯 Formål
Sikre at `status: PASSED` i evidens og opgavestempling repræsenterer en sand, uopnåelig-ved-en-fejl verifikationsgaranti:
1. Gøre `PASSED` til en strikt domæne-invariant i `runner.py` og `cli.py`: en kørsel kan KUN opnå `PASSED`, hvis samtlige påkrævede tjek er gennemført med exit code 0, og der er 0 uafklarede acceptkriterier.
2. Forhindre at manglende værktøjer (exit code 127 `command not found`) i valgfrie eller påkrævede lag producerer en falsk positiv `PASSED` rapport.
3. Nedgradere målrettede testkørsler (`--test-target`) til `status: PARTIAL` / ikke-attesterende, så en enkelt test aldrig kan stabilisere en opgave eller udstede fuld evidens.

## 📋 Acceptance Criteria
- [x] Definere eksplicit lagsemantik (`REQUIRED`, `OPTIONAL`, `SKIPPED`, `UNAVAILABLE`, `TIMED_OUT`, `ERROR`) i `features/gauntlet/models.py` og `runner.py`.
- [x] Sikre at `GauntletRunner` fejler eller markerer kørslen `FAILED`, hvis et påkrævet tjek fejler eller returnerer exit 127.
- [x] Forhindre opgavestempling (`status: stable`), hvis der resterer uafklarede acceptkriterier (`unresolved_criteria > 0`).
- [x] Ændre `--test-target` i `cli.py` til altid at markere evidens som `PARTIAL` og afvise stempling af opgavepakker.
- [x] Tilføje regressionstests i `tests/features/test_gauntlet.py` og `tests/test_cli.py`, der afprøver false-pass probes og målrettede test-forsøg.
- [x] Tilføje mutation-tests i `tools/mutants.py` for at dræbe eventuelle omgåelser af invariant-tjekkene.

## 🚫 Must NOT
- Må IKKE tillade `status: PASSED` hvis et eneste påkrævet tjek har `passed: false` eller `exit_code != 0`.
- Må IKKE opdatere opgavens frontmatter til `status: stable` under en partiel/målrettet testkørsel.

## 📝 Revisions
- 2026-08-24: Oprettet som opfølgning på code review findings EVI-02 og EVI-03 (P0).

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `python3 tools/mutants.py`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli verify --task-id 014-strict-verification-invariants-and-failure-safe-runner`
