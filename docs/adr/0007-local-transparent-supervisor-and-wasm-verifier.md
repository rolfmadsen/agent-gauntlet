---
type: Architectural Decision Record
title: 'ADR 0007: Local Transparent Supervisor with Embedded WASM Policy and Privilege Separation'
status: stable
tags:
- architecture
- adr
- supervisor
- wasm
- systemd
- security
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-30T09:16:00Z'
verified: []
---

# 7. Local Transparent Supervisor with Embedded WASM Policy & Privilege Separation

**Status**: `accepted` (Extends ADR 0005 and ADR 0006)  
**Date**: `2026-08-30`  

## Context
ADR 0005 decoupled local unsigned reports from authoritative CI attestations because unprivileged local executions cannot establish an independent trust boundary against a process running as the same OS user. While this truthfully documented local limitations, developers need strong local provenance and tamper-evident enforcement during AI-agent coding sessions before pushing to remote CI.

Furthermore, running raw gatekeeper hooks in Python inside IDE processes introduces startup latency and couples the agent harness to the host system's Python runtime.

## Decision
We introduce a local, transparent supervisor architecture with an embedded WebAssembly verifier and clean platform seams:

1. **Three-Tier Assurance Model**:
   - `LOCAL_UNSUPERVISED`: Fast-feedback unsigned report for cooperative drift detection.
   - `LOCAL_SUPERVISED` (NEW): Signed local verification report issued by a privilege-separated supervisor with ephemeral task certificates and hash-chained session logs.
   - `CI_ATTESTED`: Sigstore OIDC / in-toto attestation produced strictly within a protected CI runner.

2. **Zero Ambient Authority WASM Policy Component**:
   Policy evaluation (task binding, fine-grained capability checks) is compiled to a deterministic WebAssembly component governed by a versioned WIT contract (`wit/gauntlet_policy.wit`). The component has zero access to filesystems, network, system clocks, random sources, or private cryptographic keys.

3. **Supervisor Key Custody**:
   Ephemeral task keys and installation identity are owned strictly by the supervisor in a protected OS key store (`0700`/`0600` permissions) outside the workspace. The LLM agent and workspace scripts have zero access to private keys. No generic `SignArbitraryPayload` RPC oracle exists.

4. **Isolated Sandbox Runner Seam**:
   Verification checks and tests execute against a frozen workspace snapshot in an unprivileged sandbox (Linux `bwrap` with unshared network and read-only source binds).

5. **On-Demand Socket Activation & Platform Seams**:
   On Linux, the supervisor integrates with `systemd` socket activation (`agent-gauntlet.socket` & `agent-gauntlet.service`), starting on-demand without keeping terminal processes open. OS-specific lifecycle, IPC, sandboxing, and key storage are isolated behind narrow platform seams (`ServiceLifecycleSeam`, `IpcTransportSeam`, `SandboxRunnerSeam`, `KeyProviderSeam`).

## Consequences
- **Positive**: Establishes genuine local execution provenance and fail-closed gatekeeping on the developer's machine.
- **Positive**: Delivers zero-friction DX—developers initialize once via NPX and work normally in their IDE without manually starting daemons or copying keys.
- **Positive**: Sub-50ms warm hook evaluation latency via local IPC.
- **Positive**: Decouples the control plane from host Python installations.
- **Scope**: Reference implementation in v0.4.0 is Linux (Pop!_OS/systemd/bwrap). Native macOS (`launchd`) and Windows (`SCM`) support is isolated behind platform seams for future releases (Tasks 036 & 037).
