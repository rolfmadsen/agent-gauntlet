---
type: Task Package
title: 'Task 035: Local Transparent Supervisor with WASM Verifier'
description: 'Implementering af lokal, privilegie-adskilt supervisor med deterministisk WASM-policy og systemd socket activation for Linux.'
status: stable
tags:
- task
- supervisor
- wasm
- systemd
- linux
- security
- gauntlet
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-30T09:07:00Z'
verified:
- by: 'process:gauntlet-v0.4.0'
  at: '2026-08-30T09:19:00Z'
  note: 'Alle 7 gauntlet lag passeret inkl. 268 tests, pyright, ruff, 54/54 mutants og source state binding'
---

# Task 035: Local Transparent Supervisor with WASM Verifier

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-30`  

## 🎯 Formål
Implementere en lokal supervisorarkitektur, hvor en udvikler kan initialisere Agent Gauntlet én gang via NPX og derefter anvende Google Antigravity normalt uden:
1. Separat manuel start af en `.wasm`-fil eller supervisor-proces.
2. Manuel task-start for hver enkelt opgave.
3. En terminal der skal holdes åben i baggrunden.
4. Afhængighed af en global Python-installation til Agent Gauntlets kontrolplan.
5. Task-nøgler eller autoritativ evidens placeret i projektets workspace.

Referenceplatform for v0.4.0 er **Linux (Pop!_OS / Ubuntu) med systemd socket activation** og **Bubblewrap (`bwrap`) isolation**.

## 📋 Acceptance Criteria
- [x] **WASM Policy & WIT ABI**:
  - [x] Oprette `wit/gauntlet_policy.wit` definerende capability-request, enforcement-context og policy-decision.
  - [x] Kompilere deterministisk policy-kerne til `.wasm` med nul ambient authority (ingen FS, netværk, ur, random eller nøgler).
  - [x] Enhedstests beviser at manipuleret WASM eller ukendt schema afvises fail-closed.
- [x] **Supervisor Core & Key Custody**:
  - [x] Task Session FSM (`DISCOVERED -> ACTIVE -> VERIFYING -> PASSED | FAILED | INVALIDATED -> CLOSED`).
  - [x] Protected Key Provider genererer installation identity og ephemeral task keys/certificates uden for workspace.
  - [x] Append-only, hash-kædet session event log.
  - [x] RPC overflade (`GetStatus`, `BeginOrResumeSession`, `EvaluateToolCall`, `RequestVerification`). Ingen generisk `SignArbitraryPayload`.
- [x] **Linux Platform Seam & Socket Activation**:
  - [x] `agent-gauntlet.socket` og `agent-gauntlet.service` installer med `SD_LISTEN_FDS_START` (FD 3) støtte.
  - [x] Bubblewrap (`bwrap`) runner afvikler verifikationschecks mod et frosset workspace-snapshot uden netværksadgang.
- [x] **Antigravity Hook Shim & NPX Bootstrapper**:
  - [x] Global ultra-fast IPC hook-shim (p95 < 50ms) til Antigravity payloads (`PreInvocation`, `PreToolUse`, `PostToolUse`, `Stop`).
  - [x] `@agent-gauntlet/cli` NPX wrapper understøtter `init`, `status`, `doctor`, `repair`, `upgrade`, `uninstall` uden Python-krav.
- [x] **Offline Verifier & E2E Integration**:
  - [x] Offline verifier validerer `LOCAL_SUPERVISED` rapport uden adgang til private nøgler.
  - [x] Fuld E2E test på Linux beviser komplet installations- og verifikationsflow.
  - [x] Opdateret `spec.md`, `CONTEXT.md`, `CODING_STANDARDS.md` og ADR 0007.

## 🚫 Must NOT
- LLM-agenten må ALDRIG kontrollere supervisorens private keys, WASM-digest, event log eller signeringsoperationen.
- Repositorykode eller testscripts må ALDRIG køre med supervisorens privilegier.
- Supervisoren må IKKE indeholde en generisk `SignArbitraryPayload` operation.
- Må IKKE antage eller kræve global Python på hosten til kontrolplanet.

## 📝 Revisions
- 2026-08-30: Oprettet som hovedopgave for Agent Gauntlet v0.4.0 (Lokal Supervisor & WASM-verifier).
- 2026-08-30: Fuld implementering af Phase 1-5 afsluttet og verificeret med 100% gauntlet pass.

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `sh tools/gauntlet.sh`
- `node packages/agent-gauntlet/bin/agent-gauntlet.js status`
- Offline rapport-verifikation med negativ kontrol.
