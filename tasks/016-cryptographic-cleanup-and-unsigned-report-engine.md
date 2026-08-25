---
type: Task Package
title: 'Task 016: Cryptographic Cleanup & Unsigned Verification Report Engine'
description: 'Fjernelse af DEFAULT_KEY og lokal HMAC-forsegling, indførelse af unsigned verification-report.json v2 og fail-closed håndtering af legacy evidens'
status: stable
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-25T15:39:00Z'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-08-25T16:03:36Z'
tags:
- evidence
- cryptographic-cleanup
- unsigned-report
- security
- okf
sources:
- id: adr-0005
  resource: docs/adr/0005-two-tier-verification-and-attestation-model.md
  title: 'ADR 0005: Two-Tier Evidence and Trust Boundary Model'
---

# Task 016: Cryptographic Cleanup & Unsigned Verification Report Engine

**Status**: `DONE`  
**Intent**: `🔄 REFACTOR`  
**Oprettet**: `2026-08-25`  

## 🎯 Formål
Eliminere den falske kryptografiske selvattestering på lokale udvikler-maskiner i overensstemmelse med ADR 0005:
1. Fjerne `DEFAULT_KEY` og alle lokale HMAC-SHA256 signatur-rutiner fra standardafviklingen.
2. Omdøbe/refakturere `EvidenceAuthority` til `VerificationReportEngine` og generere `verification-report.json` (Schema v2) uden signaturfelt.
3. Håndhæve at `agent-gauntlet verify` **aldrig muterer task-filer** (`tasks/*.md`) under kørsel (Zero Self-Mutation Invariant).
4. Opgradere `agent-gauntlet check-evidence` til at validere kildedrift mod `verification-report.json` og klassificere status som `origin: LOCAL, attestation: ABSENT`.
5. Klassificere eksisterende v1 `evidence.json` som `LEGACY_UNATTESTED` og fejle autoritative porte (exit code 1), medmindre `--legacy-advisory` eksplicit angives.

## 📋 Acceptance Criteria
- [x] Slette `DEFAULT_KEY` og alle HMAC-nøgleressourcer i `src/agent_gauntlet/features/evidence/`.
- [x] Implementere `VerificationReport` model (Schema v2) i `src/agent_gauntlet/features/evidence/models.py`.
- [x] Opdatere `agent-gauntlet verify` i `src/agent_gauntlet/cli.py` til at gemme usigneret `verification-report.json` og tilhørende `evidence.md`.
- [x] Fjerne automatisk stempling/mutation af `tasks/*.md` under `verify`.
- [x] Opdatere `check-evidence` til at afvise legacy v1 `evidence.json` med exit code 1, medmindre `--legacy-advisory` er sat.
- [x] Tilføje invariant test `test_zero_local_secrets` i `tests/features/test_evidence.py`.
- [x] Opdatere samtlige unit tests, CLI tests og mutation tests til at afspejle den usignerede rapportmodel.

## 🚫 Must NOT
- Må IKKE efterlade nogen hemmelig nøgle, fallback-nøgle eller HMAC-signering i den lokale kodebase.
- Må IKKE mutere kilde- eller task-filer under kørsel af `verify`.
- Må IKKE tillade at legacy v1 HMAC-filer består autoritative valideringsporte.

## 📝 Revisions
- 2026-08-25: Oprettet iht. godkendt arkitekturplan for Two-Tier Evidence Model (P0).

## 🧪 Verifikation
- `PYTHONPATH=src /usr/bin/python3 -m unittest discover tests`
- `/usr/bin/python3 tools/mutants.py`
- `sh tools/gauntlet.sh`
