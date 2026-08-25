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
verified:
- by: agent-gauntlet/gauntlet-v1
  at: '2026-08-25T20:26:00Z'
  layers: 7
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
**Oprettet**: `2026-08-25`  

## 🎯 Formål
Lukke samtlige P0- og arkitekturfund fra den uafhængige audit af commit `81d0751`:
1. **Kryptografisk Sigstore DSSE Verifikation**: Ægte ECDSA/RSA signaturverifikation over DSSE Pre-Authentication Encoding (PAE), x509 Fulcio certifikatparsing og OIDC extension claim extraction (`1.3.6.1.4.1.57264.1.*`). Afvise alle opdigtede mock-signaturer (`INVALID`).
2. **Håndhævelse af Trust Policy Invarianter**: `minimum_origin` (afvise `LOCAL` under `CI_PROTECTED`), `allowed_runner_environments`, og strikt krav om `PASSED` verdict, `VALID` attestation og `ACCEPTED` decision.
3. **Officielt Google Antigravity Hooks Schema**: Migrere `.agents/hooks.json` og `plugins/agent-gauntlet/hooks.json` til navngivne top-level hooks med `PreToolUse` matcher/hooks-array, og implementere komplet strukturel validering i `AntigravityPluginValidator`.
4. **Skærpet Fail-Closed Gatekeeper**: Robust parsing der blokerer `git -C . push`, `git clean -d -f`, `printf x >src/pwn.py`, shell-redirections og inline Python-writes uden aktiv task.
5. **GitHub Actions Secure Use Hardening**: Faste 40-tegns commit-SHA'er på alle actions, least privilege separation, og verificeret artefakt-integritet i `attest`-jobbet.
6. **Manifest & Policy Drift Binding**: `check-evidence` og `check-attestation` verificerer både `source_manifest_digest`, `policy_digest` (beskytter `.agents/`, `.github/`, `spec.md`, `CONTEXT.md`, ADRs) og `config_digest`.
7. **Pakke-Arkitektur Refactoring (ADR 0001)**: Slanke `cli.py` ved at uddelegere verifikations- og task-håndtering til `features/evidence/verifier.py` og `task_resolver.py`, samt fjerne resterende HMAC-referencer i `ROADMAP.md` og plugin README.

## 📋 Acceptance Criteria
- [x] `AttestationEngine` verificerer Sigstore Bundle v0.2 / v0.3 kryptografisk via ECDSA SHA-256 og RSA over DSSE PAE bytes, parser Fulcio x509 certifikater og OIDC extensions, og afviser opdigtede signaturer som `INVALID`.
- [x] `TrustPolicyEngine` afviser `LOCAL` rapporter når `minimum_origin = CI_PROTECTED` og håndhæver `allowed_runner_environments`.
- [x] `.agents/hooks.json` og `plugins/agent-gauntlet/hooks.json` følger det officielle Google Antigravity schema (`{"agent-gauntlet-gatekeeper": {"PreToolUse": [...]}}`).
- [x] `AntigravityPluginValidator` validerer den komplette hooks-struktur mekanisk og fanger ulovlige hooks, manglende handlers og ugyldige felter.
- [x] `PolicyEngine` i `gatekeeper.py` blokerer `git -C . push`, `git clean -d -f`, `printf x >src/pwn.py`, og shell/python skrivninger til beskyttede mapper uden aktiv task.
- [x] `.github/workflows/ci.yml` pinner alle actions til 40-tegns commit-SHA'er og binder kørslen til task 023.
- [x] `check-evidence` og `check-attestation` fejler hvis `.agents/hooks.json`, `.github/`, eller `gauntlet.toml` er ændret (policy drift).
- [x] `cli.py` er refaktoreret til ren orkestrering (< 300 linjer) med `features/evidence/verifier.py` og `task_resolver.py`.
- [x] Resterende HMAC-referencer i `ROADMAP.md` og `plugins/agent-gauntlet/README.md` er fjernet.
- [x] 0 Pyright fejl, 0 Ruff fejl, 100% mutants killed, alle tests bestået.

## 🚫 Must NOT
- Must NOT tillade mock-signaturer eller ikke-kryptografisk verificerede attestationer at opnå `VALID` status.
- Must NOT tillade `LOCAL` rapporter at bestå under en `CI_PROTECTED` trust policy.
- Must NOT checkout kandidatkode i det privilegerede CI-signeringsjob.
- Must NOT tillade flydende tags i GitHub Actions.
