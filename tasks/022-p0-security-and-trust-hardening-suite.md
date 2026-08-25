---
type: Task Specification
title: 'Task 022: P0 Security, Policy Engine and Attestation Hardening Suite'
status: stable
tags:
- security
- attestation
- gatekeeper
- manifest
- task
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-25T19:25:00Z'
verified:
- by: antigravity/gemini-3.7-flash
  at: '2026-08-25T19:32:00Z'
sources:
- id: adr-0005
  resource: docs/adr/0005-two-tier-verification-and-attestation-model.md
  title: 'ADR 0005: Two-Tier Evidence and Trust Boundary Model'
- id: adr-0006
  resource: docs/adr/0006-multi-harness-policy-adapter-contract.md
  title: 'ADR 0006: Multi-Harness Policy Adapter Contract'
---

# Task 022: P0 Security, Policy Engine and Attestation Hardening Suite

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-25`  

## 🎯 Formål
Lukke samtlige 6 P0-fund fra den formelle sikkerheds- og tillidsaudit:
1. **Manifest Hardening**: Længdepræfikset eller null-byte format, kun executable bit (0/1), og binding af `.agents/` og `.github/` filer.
2. **Fail-Closed Policy Engine & Antigravity Hook Schema**: Deny-by-default på ukendte tool-calls, blokering af destruktiv git (`reset --hard`, `clean -fdx`), forbud mod shell-skrivning til `src/` uden opgave, og officiel Google Antigravity `PreToolUse` hook-kontrakt.
3. **Zero False-PASSED & Invariant Enforcement**: Håndhæve $Digest_{pre} == Digest_{post}$ (forbud mod self-mutation under test), og fejlende optional lag markerer rapporten `PARTIAL` i stedet for `PASSED`.
4. **Ægte Sigstore DSSE Attestation Engine**: Parser og verificerer Sigstore Bundle v0.2 / in-toto DSSE envelopes (`dsseEnvelope`, `verificationMaterial`), afviser manipulerede payloads, og validerer OIDC issuer, subject digest og repo.
5. **Hermetisk CI Pipeline**: Fjerne checkout af kandidatkode i `attest`-jobbet, så signeringsjobbet er 100% uafhængigt.

## 📋 Acceptance Criteria
- [x] Manifest formatering beskytter mod newline-injektion og hasher kun executable-bit (0 eller 1).
- [x] `.agents/hooks.json` og `.github/` filer inkluderes i canonical manifest / policy checks.
- [x] `PolicyEngine` afviser ukendte værktøjer, ukendte commands, destruktiv git (`clean`, `reset --hard`) og shell-skrivninger til beskyttede stier.
- [x] `.agents/hooks.json` skema tilpasses officiel Google Antigravity `PreToolUse` kontrakt.
- [x] `verify` fejler hvis $Digest_{pre} \ne Digest_{post}$, og fejlende checks markerer kørslen `PARTIAL` eller `FAILED`.
- [x] `AttestationEngine` understøtter Sigstore Bundle v0.2 med base64 DSSE in-toto payload.
- [x] `.github/workflows/ci.yml` `attest`-job fjerner checkout og downloader kun `verification-report` artifact.
- [x] 0 Pyright fejl, 0 Ruff fejl, 100% mutants killed, alle tests bestået.

## 🚫 Must NOT
- Must NOT stole på ukontrollerede bruger-/agent-payloads uden type-snævring og schema-validering.
- Must NOT foretage checkout af kandidatkode i et privilegeret CI-signeringsjob.
- Must NOT tillade at en testkørsel ændrer kildekoden uden at rapportere det som fejl.
