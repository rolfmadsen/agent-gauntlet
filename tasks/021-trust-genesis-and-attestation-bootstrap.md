---
type: Task Package
title: 'Task 021: Trust Genesis & Attestation Bootstrap Verification'
description: 'Etablering af tillidsgenesis, uafhængig validering af kandidatrapporter i CI og deny-by-default TrustPolicy motor'
status: stable
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-25T15:55:00Z'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-08-25T16:03:36Z'
tags:
- attestation
- trust-genesis
- trust-policy
- sigstore
- okf
sources:
- id: adr-0005
  resource: docs/adr/0005-two-tier-verification-and-attestation-model.md
  title: 'ADR 0005: Two-Tier Evidence and Trust Boundary Model'
---

# Task 021: Trust Genesis & Attestation Bootstrap Verification

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-25`  

## 🎯 Formål
Forhindre cirkulær selv-attestering (hvor en kandidat-version attesterer sin egen rapport med egen ukontrolleret kode) i henhold til ADR 0005:
1. Definere `TrustPolicy` model og evalueringsmotor med streng deny-by-default semantik.
2. Definere `AttestationBundle` og `AttestationStatus` håndtering for Sigstore / GitHub OIDC attestations.
3. Sikre at attesteringsvalidering adskiller `verification_result` (PASSED/FAILED), `attestation_status` (ABSENT/VALID/INVALID) og `trust_decision` (ACCEPTED/POLICY_REJECTED).
4. Etablere en uafhængig valideringsrutine, der kan verificere kandidatrapportens integritet og kildedigest uden at eksekvere kandidatens egen kodebase.

## 📋 Acceptance Criteria
- [x] Implementere `TrustPolicy` og `TrustDecision` i `src/agent_gauntlet/features/evidence/trust_policy.py`.
- [x] Implementere `AttestationBundle` og `AttestationEngine` i `src/agent_gauntlet/features/evidence/attestation.py`.
- [x] Sikre at en gyldig signatur på en rapport med `verdict: FAILED` resulterer i `attestation_status: VALID`, men `verification_result: FAILED` og dermed afvises til release/stabilisering.
- [x] Sikre at ukendte OIDC issuers eller uvedkommende repositories afvises med `trust_decision: POLICY_REJECTED`.
- [x] Tilføje sort-boks accepttests og invariant-tests i `tests/features/test_attestation.py`.
- [x] Opretholde 100% mutation kill-rate i `tools/mutants.py`.

## 🚫 Must NOT
- Må IKKE tillade kandidatkode at signere eller attestere uden uafhængig validering af rapport og manifest.
- Må IKKE blande `verification_result` sammen med `attestation_status` (en mislykket test er stadig en validt underskrevet erklæring om fiasko).
- Må IKKE have permissive default-tillid (enhver manglende eller uoverensstemmende trust-policy regel skal afvise).

## 📝 Revisions
- 2026-08-25: Oprettet som forudsætning for Task 019 og Task 020 (P0 trust bootstrap milestone).

## 🧪 Verifikation
- `PYTHONPATH=src /usr/bin/python3 -m unittest tests/features/test_attestation.py`
- `/usr/bin/python3 tools/mutants.py`
- `sh tools/gauntlet.sh`
