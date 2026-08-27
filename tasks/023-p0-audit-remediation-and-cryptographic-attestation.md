---
type: Task Package
title: 'Task 023: P0 Audit Remediation, Cryptographic Sigstore DSSE & Official Hook Schema'
description: 'Lukning af P0 audit-fund vedr. DSSE-signaturverifikation, trust policy, Antigravity hooks schema og CI hardening'
status: stable

tags:
- security
- sigstore
- dsse
- antigravity
- hooks
- github-actions
- gatekeeper
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-25T20:17:00Z'
verified: []
sources:
- id: adr-0001
  resource: docs/adr/0001-package-by-feature-architecture.md
  title: 'ADR 0001: Package-by-Feature Architecture'
- id: adr-0005
  resource: docs/adr/0005-two-tier-verification-and-attestation-model.md
  title: 'ADR 0005: Two-Tier Evidence and Trust Boundary Model'
- id: adr-0006
  resource: docs/adr/0006-multi-harness-policy-adapter-contract.md
  title: 'ADR 0006: Multi-Harness Policy Adapter Contract'
---

# Task 023: P0 Audit Remediation, Cryptographic Sigstore DSSE & Official Hook Schema

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-25` (Genåbnet `2026-08-27` efter opfølgnings-review, afsluttet `2026-08-27`)  

## 🎯 Formål
Lukke samtlige P0-, P1- og P2-fund fra den uafhængige audit af commit `81d0751` samt re-audit af `b9a590f`:
1. **GitHub-Native & Sigstore Trust-Arkitektur**: `actions/attest` udsteder og `gh attestation verify` verificerer. `agent-gauntlet` evaluerer domænepolitik ovenpå verificerede attestationer. Afvise alle selvdeklarerede mock-bundles uden DSSE envelope som `INVALID`.
2. **Kandidat N Trust & Validering**: Uafhængig validering i CI-signeringsjobbet af checks, obligatoriske resultater og alle digests bundet til `${{ github.sha }}`.
3. **Fail-Closed & Zero False-PASSED Invarianter**: Afvise rapporter med 0 kriterier, 0 checks, task drift eller manglende/drifede digests (`source_manifest`, `policy`, `config`, `task`).
4. **Origin & Provenance Model**: Rapporter angiver kun `LOCAL` eller `CI_UNPRIVILEGED`. Beskyttet origin `CI_PROTECTED` udledes fra verificeret attestation.
5. **Gatekeeper & Task Domain**: Dokumentere Gatekeeper som kooperativ UX/proces-guardrail, udtrække task contract parsing til dedikeret modul, og tillade kun eksplicitte aktive task statusser (`ACTIVE`, `IN_PROGRESS`, osv.).
6. **Antigravity Hooks Schema**: Fuld strukturel validering med understøttelse af `"*"` og `""` som match-all uden regex compiler fejl.
7. **Slank Pakke-Arkitektur (ADR 0001)**: Slanke `cli.py` til under 250 linjer ved at uddelegere forretningslogik til feature moduler.
8. **Diagnostics & Formatering**: Binde diagnostics findings i schema v2 rapporten, køre `ruff format --check .` i Gauntlet Layer 1, og præcisere mutationsdækning som 46/46 kuraterede mutanter.

## 📋 Acceptance Criteria
- [x] 1. En bundle uden DSSE/cert/timestamps eller med kun opdigtet `status: VALID` afvises som `INVALID`.
- [x] 2. En lokalt selvsigneret dummy-bundle afvises under strict trust policy.
- [x] 3. CI `attest`-jobbet validerer uafhængigt hele rapportkontrakten (non-empty criteria, non-empty checks, alle obligatoriske PASSED med exit code 0, og alle digests) mod `${{ github.sha }}` før signering.
- [x] 4. Nul kriterier, nul checks, manglende digests og task-drift afvises fail-closed gennem CLI- og verifier-entrypoints.
- [x] 5. Den legitime CI-rapport kan opnå release eligibility via verificeret attestation uden selvangivet `CI_PROTECTED`-felt i rapporten.
- [x] 6. Gatekeeperens dokumenterede rolle svarer til dens faktiske kooperative guardrail-model, og `is_task_active` afviser `DRAFT`, `REJECTED` og status-løse tasks.
- [x] 7. Task-parsing og status-semantik er udtrukket til en selvstændig `features/tasks/` modul uden cirkulær afhængighed til gatekeeper.
- [x] 8. `AntigravityPluginValidator` accepterer `matcher: "*"` og `matcher: ""` som gyldige match-all filtre, validerer non-empty root og events, og tjekker positivt integer timeout.
- [x] 9. `src/agent_gauntlet/cli.py` er refaktoreret til ren dispatch/orkestrering (< 250 linjer).
- [x] 10. `verification-report.json` serialiserer diagnostic findings, `tools/gauntlet.sh` kører `ruff format --check .`, og 0 Pyright/Ruff fejl med 46/46 kuraterede mutanter killed.


## 🚫 Must NOT
- Must NOT tillade mock-signaturer eller ikke-kryptografisk verificerede attestationer at opnå `VALID` status.
- Must NOT tillade `LOCAL` rapporter at bestå under en `CI_PROTECTED` trust policy uden gyldig verificeret attestation.
- Must NOT tillade checkout af kandidatkode i det privilegerede CI-signeringsjob.
- Must NOT tillade flydende tags i GitHub Actions.
- Must NOT tillade 0 kriterier eller 0 checks at give `PASSED` verdict.

## 📝 Revisions
- **2026-08-25**: Oprindelig Task 023 oprettet for P0 remediation af commit `81d0751`.
- **2026-08-27**: Genåbnet efter re-audit af commit `b9a590f`. Krav opdateret til GitHub-native / multi-CI trust model, fail-closed bindings-invarianter, gatekeeper status-stramning, Antigravity wildcard matchers og < 250 linjers CLI refactoring.
