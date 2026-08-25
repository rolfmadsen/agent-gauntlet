---
type: Task Package
title: 'Task 020: Detached Attestation Verification & Deny-by-Default CLI Enforcement'
description: 'Implementering af agent-gauntlet check-attestation CLI kommando med ortogonal evaluering og TrustPolicy validering'
status: stable
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-25T15:54:00Z'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-08-25T16:03:36Z'
tags:
- cli
- check-attestation
- trust-policy
- sigstore
- release-gate
- okf
sources:
- id: adr-0005
  resource: docs/adr/0005-two-tier-verification-and-attestation-model.md
  title: 'ADR 0005: Two-Tier Evidence and Trust Boundary Model'
---

# Task 020: Detached Attestation Verification & Deny-by-Default CLI Enforcement

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-25`  

## 🎯 Formål
Færdiggøre todelt evidensmodel i CLI'en med `check-attestation`:
1. Implementere `agent-gauntlet check-attestation` CLI underkommando.
2. Evaluer de tre ortogonale dimensioner:
   - `verification_result`: `PASSED | FAILED | ERROR | INCOMPLETE | SKIPPED`
   - `attestation_status`: `ABSENT | VALID | INVALID`
   - `trust_decision`: `ACCEPTED | POLICY_REJECTED`
   - `release_eligible`: `PASSED AND attestation_status == VALID AND trust_decision == ACCEPTED`
3. Understøtte bruger-/organisationsdefineret `--trust-policy <file>` (deny-by-default).
4. Tilbyde struktureret JSON-output (`--json`) og maskinlæsbare fejldiagnoser.

## 📋 Acceptance Criteria
- [x] Implementere `check-attestation` subparser og handler i `src/agent_gauntlet/cli.py`.
- [x] Sikre at afprøvning af en attesteret fiasko (`verdict: FAILED` med valid signatur) rapporterer `attestation_status: VALID`, `trust_decision: ACCEPTED`, men returnerer exit code 1 og `release_eligible: False`.
- [x] Sikre at manglende attestation uden `--allow-unattested` afvises med exit code 1.
- [x] Sikre at uautoriserede OIDC signers afvises med exit code 1 og `trust_decision: POLICY_REJECTED`.
- [x] Tilføje CLI tests i `tests/test_cli.py`.
- [x] Køre fuld verifikations-gauntlet og mutationstests.

## 🚫 Must NOT
- Må IKKE fejle åbent ved manglende trust policy-fil eller ukendte felter.
- Må IKKE blande `verification_result` sammen med `attestation_status`.
- Må IKKE lade lokal uattesteret rapport passere som release-godkendt uden eksplicit `--allow-unattested`.

## 📝 Revisions
- 2026-08-25: Oprettet som afsluttende del af Phase 2 to-tier evidens milestone.

## 🧪 Verifikation
- `PYTHONPATH=src /usr/bin/python3 -m unittest discover tests`
- `/usr/bin/python3 tools/mutants.py`
- `sh tools/gauntlet.sh`
