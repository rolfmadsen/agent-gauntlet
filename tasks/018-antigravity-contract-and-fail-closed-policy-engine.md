---
type: Task Package
title: 'Task 018: Antigravity Contract Verification & Fail-Closed Policy Engine'
description: 'Integrationstest af Antigravity denial-protokol, refakturering til PolicyEngine, CapabilityRequest unioner og fail-closed hook eksekvering'
status: stable
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-25T15:39:00Z'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-08-25T16:03:36Z'
tags:
- policy-engine
- adapters
- antigravity
- fail-closed
- okf
sources:
- id: adr-0006
  resource: docs/adr/0006-multi-harness-policy-adapter-contract.md
  title: 'ADR 0006: Multi-Harness Policy Adapter Contract and Trusted Context'
---

# Task 018: Antigravity Contract Verification & Fail-Closed Policy Engine

**Status**: `DONE`  
**Intent**: `🔄 REFACTOR`  
**Oprettet**: `2026-08-25`  

## 🎯 Formål
Etablere en robust, type-sikker og fail-closed policy-motor i overensstemmelse med ADR 0006:
1. Verificere den faktiske Google Antigravity hook denial-kontrakt via subprocess-integrationstests (`{"decision": "deny", "reason": "..."}` på stdout samt exit code 1).
2. Refakturere `features/hooks/gatekeeper.py` til en ren `PolicyEngine`, der evaluerer `CapabilityRequest` diskriminerede unioner mod en uforanderlig `TrustedEnforcementContext`.
3. Fjerne alle import-afhængigheder fra `features/hooks/` til `features/evidence/models.py`.
4. Sikre at korrupt, tom eller uunderstøttet JSON-input på stdin altid fejler lukket (`decision: deny`, exit code 1).
5. Implementere en genbrugelig adapter conformance-testsuite.

## 📋 Acceptance Criteria
- [x] Tilføje subprocess integrationstests der verificerer Antigravity denial-adfærd.
- [x] Implementere `TrustedEnforcementContext` og `CapabilityRequest` diskriminerede typer.
- [x] Refakturere `AntigravityAdapter` til at oversætte vendor payloads til `CapabilityRequest` uden at lade indgående data overskrive betroet kontekst.
- [x] Sikre at `hook.py` og CLI entrypoints returnerer exit code 1 og `decision: deny` på korrupte inputs.
- [x] Fjerne unødvendige model-koblinger fra hooks-modulet.

## 🚫 Must NOT
- Må IKKE fejle åbent (returnere exit code 0 / allow) ved ukendte, korrupte eller tomme inputs.
- Må IKKE acceptere betroede autoritetsfelter (`workspace_root`, `task_id`) direkte fra ufiltrerede agent payload-argumenter.

## 📝 Revisions
- 2026-08-25: Oprettet iht. godkendt arkitekturplan for Multi-Harness Policy Adapter Contract (P0).

## 🧪 Verifikation
- `PYTHONPATH=src /usr/bin/python3 -m unittest tests/features/test_hooks.py tests/features/test_adapter_antigravity.py`
- `/usr/bin/python3 tools/mutants.py`
