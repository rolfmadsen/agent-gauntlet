---
type: Task Package
title: 'Task 033: Changed-Line Differential Coverage Gauntlet Layer'
description: 'Implementation af differentiel dækningsanalyse (diff-cover), der gennemtvinger 100% test- og branch-dækning på udelukkende ændrede linjer i git diff.'
status: draft
tags:
- task
- coverage
- diff-cover
- gauntlet
- verification
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-29T10:50:00Z'
---

# Task 033: Changed-Line Differential Coverage Gauntlet Layer

**Status**: `TODO`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-29`  

## 🎯 Formål
Implementere præcisions-verifikationslag for **Changed-Line Differential Coverage** (`diff-cover`) jf. [ROADMAP.md](ROADMAP.md) (Rangering 7):
1. Isolere den aktuelle Git-diff (eller workspace snapshot-diff) og beregne testdækning for *udelukkende* de linjer og branches, der er rørt ved i opgaven.
2. Gennemtvinge 100% dækning på ny kode og fejlrettelser uden at kræve 100% dækning på hele den eksisterende kodebase.
3. Integrere differentiel dækning som et deklarativt lag i `gauntlet.toml` og `GauntletRunner`.

## 📋 Acceptance Criteria
- [ ] Oprette `src/agent_gauntlet/features/coverage/` vertical slice til parsing af git diff og dækningsrapporter (f.eks. `coverage.py`, `lcov`, `llvm-cov`).
- [ ] Beregne diff-coverage procentdel for ændrede/tilføjede linjer.
- [ ] Tilføje `diff_coverage_threshold` konfiguration i `gauntlet.toml` (standard 100%).
- [ ] Integrere diff-coverage tjek i `agent-gauntlet verify` og registrere dækningsstatistikker i `verification-report.json`.
- [ ] Tilføje sort-boks accepttests i `tests/features/test_diff_coverage.py`.
- [ ] Tilføje mutation testing i `tools/mutants.py` med 100% kill-rate.
- [ ] `agent-gauntlet okf validate` godkender alle oprettede filer.

## 🚫 Must NOT
- Må IKKE fejle hvis der ikke er nogen kodeændringer (0 ændrede linjer skal bestå som no-op).
- Må IKKE bryde fail-closed princippet ved ufuldstændige dækningsdata.

## 📝 Revisions
- 2026-08-29: Oprettet som del af næste udviklingsepoke baseret på ROADMAP.md Rangering 7.

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `PYTHONPATH=src python3 tools/mutants.py`
- `sh tools/gauntlet.sh`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli verify`
