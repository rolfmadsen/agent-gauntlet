---
type: Task Package
title: 'Task 019: Two-Job CI Verification & Attestation Pipeline'
description: 'Opdeling af CI i uprivilegeret verify-job og privilegeret attest-job med actions/attest og SLSA provenance'
status: stable
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-25T15:52:00Z'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-08-25T16:03:36Z'
tags:
- ci
- github-actions
- actions-attest
- slsa
- trust-boundary
- okf
sources:
- id: adr-0005
  resource: docs/adr/0005-two-tier-verification-and-attestation-model.md
  title: 'ADR 0005: Two-Tier Evidence and Trust Boundary Model'
---

# Task 019: Two-Job CI Verification & Attestation Pipeline

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-25`  

## 🎯 Formål
Etablere en hård isolation mellem verifikationsudførelse og kryptografisk attestering i CI:
1. **Uprivilegeret `verify` job**: Kører verifikationslag, mutationstests og genererer `verification-report.json` med minimale rettigheder (`contents: read`, `id-token: none`).
2. **Privilegeret `attest` job**: Kører kun på beskyttede branches/tags med `id-token: write` og `attestations: write`. Downloader rapporten, validerer kildedigest uafhængigt, og genererer en Sigstore OIDC attestering via `actions/attest@v2`.
3. Sikre at CI-skabeloner i `scaffolder.py` og repository-workflowet følger denne to-job arkitektur.

## 📋 Acceptance Criteria
- [x] Opdatere `.github/workflows/ci.yml` til en to-job pipeline (`verify` og `attest`).
- [x] Konfigurere `verify`-jobbet med minimale rettigheder (`contents: read`) og uploade `verification-report.json`.
- [x] Konfigurere `attest`-jobbet med `permissions: { id-token: write, attestations: write, contents: read }`, afhængighed af `verify`, og betingelse om push til hovedbranch eller tags.
- [x] Integrere `actions/attest@v2` med `predicate-type: "https://agent-gauntlet.dev/attestation/v1"`.
- [x] Opdatere `scaffolder.py` til at understøtte CI workflow-skabelonen.
- [x] Tilføje tests i `tests/features/test_scaffold.py` og validere workflow-syntaks.

## 🚫 Must NOT
- Må IKKE give `id-token: write` eller `attestations: write` til det uprivilegerede test/verifikations-job.
- Må IKKE tillade attestering af rapporter genereret i ubeskyttede pull requests fra forks.
- Må IKKE eksekvere vilkårlig kandidatkode i det privilegerede attest-job.

## 📝 Revisions
- 2026-08-25: Oprettet som led i Phase 2 sikkerheds-milestone efter Task 021.

## 🧪 Verifikation
- `PYTHONPATH=src /usr/bin/python3 -m unittest discover tests`
- `/usr/bin/python3 tools/mutants.py`
- `sh tools/gauntlet.sh`
