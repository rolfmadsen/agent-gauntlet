---
type: Task Package
title: 'Task 038: Release Readiness and Documentation Synchronization Gate'
description: 'Implementering af automatiseret release-validering og dokumentations-synkronisering (agent-gauntlet check-release), der verificerer versionsharmoni, CHANGELOG.md og ADR-dækning før release.'
status: stable
tags:
- task
- release
- governance
- changelog
- documentation
- gauntlet
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-30T09:30:00Z'
verified:
- by: 'process:gauntlet-v0.4.0'
  at: '2026-08-30T09:33:00Z'
  note: 'Alle lag passeret inkl. test_check_release, 56/56 mutanter og check-release validering'
---

# Task 038: Release Readiness and Documentation Synchronization Gate

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-30`  

## 🎯 Formål
Etablere en mekanisk, automatiseret release-gate (`agent-gauntlet check-release`), der forhindrer *dokumentations-kløft* og forældede release-notes ved software-udgivelser:
1. **Versions-Harmoni**: Sikre at versionsnummeret i `pyproject.toml` (og `packages/agent-gauntlet/package.json` hvis til stede) stemmer 100% overens med den seneste overskrift i `CHANGELOG.md` (f.eks. `## [0.4.0]`).
2. **ADR-Integritet**: Sikre at samtlige Architecture Decision Records i `docs/adr/000*.md` er dokumenteret og linket i `README.md` og `spec.md`.
3. **Actionable Diagnostics**: Returnere strukturerede udbedringsforslag (remediation hints), hvis `CHANGELOG.md` mangler en sektion, eller hvis der er uoverensstemmelse mellem konfigurationer.
4. **Fasedeling (SRP)**: Køre udelukkende i Release & Operations fasen uden at forstyrre den daglige TDD-udviklingscyklus i `agent-gauntlet verify`.

## 📋 Acceptance Criteria
- [x] **Kerne Release Validator (`features/release/` eller `features/evidence/release_gate.py`)**:
  - [x] Implementere `check_release_readiness(workspace: Path, allow_unreleased: bool = False) -> ReleaseReadinessReport`.
  - [x] Udtrække projektets aktuelle version fra `pyproject.toml`, `package.json` og/est `Cargo.toml`.
  - [x] Parse `CHANGELOG.md` (Keep a Changelog format) og verificere at der findes en sektion for den aktuelle version (f.eks. `## [0.4.0] - YYYY-MM-DD`).
  - [x] Verificere at alle `docs/adr/*.md` (undtagen `README.md` i mappen) er refereret i `README.md` og `spec.md`.
- [x] **CLI Integration (`agent-gauntlet check-release`)**:
  - [x] Tilføje `check-release` subcommand til CLI parseren i `src/agent_gauntlet/cli.py`.
  - [x] Understøtte flag: `--workspace`, `--json`, `--allow-unreleased` (tillader `## [Unreleased]`).
  - [x] Returnere exit code `0` ved godkendt release-tilstand og `1` ved manglende release-dokumentation.
- [x] **FSM & Session Handoff Integration**:
  - [x] Opdatere `infer_next_session_role()` i `src/agent_gauntlet/features/evidence/verifier.py`, så `Release & Operations Engineer` eksplicit instrueres i at køre `agent-gauntlet check-release`.
- [x] **Multi-Stack & Robusthed**:
  - [x] Fungere transparent i rene Python-, TypeScript-, Rust- og multi-package workspaces uden falske positive.
- [x] **Gauntlet & Mutation Testing**:
  - [x] Tilføje unit- og acceptance-tests i `tests/features/test_check_release.py`.
  - [x] Tilføje syntetiske mutanter i `tools/mutants.py` og opnå 100% kill-rate.
  - [x] `agent-gauntlet okf validate` godkender alle metadata-filer.

## 🚫 Must NOT
- Må IKKE fejle hvis valgfri økosystemfiler ikke findes (f.eks. må den ikke kræve `package.json` i et rent Rust-projekt).
- Må IKKE køre som et obligatorisk lag i `agent-gauntlet verify` under almindelig TDD-udvikling (skal være en separat release-gate).
- Må IKKE ændre eksisterende kildekodefiler automatisk (skal være read-only validering).

## 📝 Revisions
- 2026-08-30: Oprettet efter identifikation af manglende mekanisk enforcement for `README.md` og `CHANGELOG.md` synkronisering ved v0.4.0 release.
- 2026-08-30: Fuld TDD-implementation fuldført med `ReleaseReadinessEngine`, CLI subcommand `check-release`, 7 nye tests og 56/56 mutanter dræbt. Status sat til DONE.

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m agent_gauntlet.cli check-release`
- `PYTHONPATH=src python3 -m unittest tests/features/test_check_release.py`
- `sh tools/gauntlet.sh`

