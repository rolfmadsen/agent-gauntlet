---
type: Task Package
title: 'Task 043: Real WASM Policy Engine & Supervisor Daemon'
description: 'Fuldbyrdelse af WebAssembly policy-komponent, compilation til wasm32-unknown-unknown, Unix Domain Socket daemon server, Antigravity Hook Shim IPC integration og stramning af aktiv task status.'
status: stable
tags:
- task
- supervisor
- wasm
- policy-engine
- antigravity
- socket-activation
- security
generated:
  by: antigravity/gemini-3.8-flash
  at: '2026-09-03T16:15:00Z'
verified:
- by: process:agent-gauntlet
  at: '2026-09-03T16:28:11Z'
---

# Task 043: Real WASM Policy Engine & Supervisor Daemon

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-09-03`  

## 🎯 Formål
Færdiggøre og fuldbyrde arkitekturen fra ADR 0007 og Task 035, så Agent Gauntlet reelt afvikler en WebAssembly (WASM) policy-motor og en aktiv lokal supervisor:
1. **WASM Crate & Kompilering**:
   - Eksponere C/WASM JSON-evaluering i `crates/gauntlet-policy-engine`.
   - Kompilere til `wasm32-unknown-unknown` og placere `policy_engine.wasm` under `src/agent_gauntlet/features/supervisor/wasm/`.
2. **WASM Verifier Runtime**:
   - Implementere reel WebAssembly-afvikling i `WasmPolicyVerifier` via Node.js V8 WebAssembly engine (med native/ctypes fallback).
   - Verificere SHA-256 digest for den indlæste WASM-binær.
3. **Supervisor Unix Domain Socket Server**:
   - Implementere `SupervisorServer` i `features/supervisor/platform/linux/server.py`, der lytter på Unix domain socket og håndterer JSON-RPC linje-for-linje med systemd socket activation støtte.
4. **Antigravity Hook IPC Integration**:
   - Forbinde `hook.py` til `AntigravityHookShim`, så PreToolUse hooks evalueres mod den kørende supervisor over IPC med fail-closed fallback.
5. **Stramning af Task-Status Semantik**:
   - Fjerne `TaskStatus.TODO` fra `ALLOWED_ACTIVE_STATUSES` i `models.py`, så kun opgaver i reel aktiv fremdrift (`ACTIVE`, `IN_PROGRESS`, `WIP`, `REOPENED`) tillader modifikation af `src/` og `tests/`.
6. **CLI Kommandoer**:
   - Tilføje `agent-gauntlet supervisor start|status` til CLI.

## 📋 Acceptance Criteria
- [x] `TaskStatus.TODO` er fjernet fra `ALLOWED_ACTIVE_STATUSES`.
- [x] `crates/gauntlet-policy-engine` har `evaluate_json` C-ABI og kompilerer fejlfrit til `policy_engine.wasm`.
- [x] `WasmPolicyVerifier` afvikler den kompilerede WASM-binær og validerer dens SHA-256 digest.
- [x] `SupervisorServer` lytter på Unix domain socket og besvarer RPC'er (`GetStatus`, `EvaluateToolCall` m.fl.).
- [x] `AntigravityHookShim` evaluerer tool-kald via supervisor IPC og fejler lukket (fail-closed) ved fejl.
- [x] `agent-gauntlet supervisor start` og `agent-gauntlet supervisor status` virker fra CLI.
- [x] Alle unit-, integration- og gauntlet-tests passerer 100% (inkl. mutationstests).

## 🚫 Must NOT
- Må IKKE fjerne eller slække på de eksisterende sikkerhedsinvarianter i PolicyEngine.
- Må IKKE fejle åbent hvis WASM/supervisor fejler (skal altid fejle lukket/fail-closed med exit code 1 og `{"decision": "deny"}`).
- Må IKKE efterlade forældreløse socket-filer eller ulukkede serverprocesser.
- Må IKKE introducere eksterne tunge pip-afhængigheder; skal udnytte maskinens eksisterende Node.js/Rust/Python infrastruktur.

## 📝 Revisions
- 2026-09-03: Oprettet efter brugergodkendelse af implementeringsplan til at realisere ægte WASM-policy og supervisor.
- 2026-09-03: Implementering fuldført. WASM engine, daemon server, CLI kommandoer og tests passerer 100%. Status ændret til DONE.
- 2026-09-03: Kritisk code review gennemført og 8 fund udbedret (robust top-level JSON lexer i Rust uden dependencer, ægte detached OS-proces i CLI daemon start, RLock trådsikkerhed i SupervisorEngine, mkdtemp 0700 fallback for nøgledepot, fail-closed fejlhåndtering uden undtagelsesmaskering, stdin streaming i WASM runner mod ARG_MAX/proceslækage, samt stale socket resilience i Antigravity-hook). Alle 7 gauntlet-lag valideret.

## 🧪 Verifikation
- `cargo test --manifest-path crates/gauntlet-policy-engine/Cargo.toml`
- `cargo build --target wasm32-unknown-unknown --release --manifest-path crates/gauntlet-policy-engine/Cargo.toml`
- `PYTHONPATH=src python3 -m unittest discover tests`
- `sh tools/gauntlet.sh`
