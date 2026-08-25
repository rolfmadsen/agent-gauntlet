---
type: Architectural Decision Record
title: 'ADR 0005: Two-Tier Evidence and Trust Boundary Model'
status: stable
tags:
- architecture
- adr
- security
- attestation
- okf
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-25T15:39:00Z'
verified: []
---

# 5. Two-Tier Evidence and Trust Boundary Model

**Status**: `accepted` (Supersedes ADR 0002)  
**Date**: `2026-08-25`

## Context
ADR 0002 introduced local HMAC-SHA256 signing of verification records using an embedded default key (`DEFAULT_KEY`). Because this key is distributed with the application, any local process or agent can generate valid HMAC signatures. Local verification cannot prove that tests were executed honestly, nor can it serve as an independent security boundary against a process running as the same OS user.

Furthermore, CI workflows previously ran verification and evidence checks in a single job without detached, identity-bound attestations, creating self-attestation loops.

## Decision
We decouple **Local Verification Reporting** from **Authoritative Attestation**:

1. **Two Distinct Artifacts**:
   - `verification-report.json`: An unsigned JSON document produced by `agent-gauntlet verify`. It records verification claims, layer outcomes, diagnostic findings, pre/post source manifest digests, and task contracts.
   - `attestation.bundle`: An optional, detached in-toto / DSSE / Sigstore attestation bundle generated strictly within a protected, privileged CI workflow. It cryptographically binds an ambient CI identity (OIDC) to the verification report and source manifest.

2. **Orthogonal Assurance Dimensions**:
   Consumers MUST evaluate verification and trust across three independent dimensions:
   - `verification_result`: `PASSED` | `FAILED` | `ERROR` | `INCOMPLETE` | `SKIPPED`
   - `attestation_status`: `ABSENT` | `VALID` | `INVALID`
   - `trust_decision`: `ACCEPTED` | `POLICY_REJECTED`
   
   Release eligibility is strictly:
   `verification_result == PASSED AND attestation_status == VALID AND trust_decision == ACCEPTED`

3. **Canonical Workspace Manifest**:
   Workspace state is captured via a deterministic SHA-256 tree manifest that works identically offline without Git. It incorporates UTF-8 normalized relative paths, file content hashes, POSIX executable permission bits, and strict symlink boundary checks to prevent workspace escapes.

4. **Independent Privileged CI Attestation Path**:
   - Pull request CI runs **unprivileged** (`permissions: contents: read`) with no OIDC tokens or signing secrets.
   - Attestation occurs exclusively on protected branches/tags (`push` to `main`, releases) in a dedicated job with `permissions: id-token: write, attestations: write`.
   - The attestation job **does not checkout or execute repository code** and never runs `tools/gauntlet.sh`. It verifies the report produced by the unprivileged job and generates the signed DSSE predicate natively via `actions/attest`.

5. **Self-Attestation Bootstrap Rule (Release N-1)**:
   A candidate release $N$ of `agent-gauntlet` cannot define its own verification criteria. Release $N$ is verified by the pinned, trusted release $N-1$ distribution in CI before the attestation workflow signs the candidate artifact.

## Consequences
- **Positive**: Eliminates all hardcoded keys and local HMAC secrets. Guarantees true cryptographic assurance tied to verifiable CI provenance.
- **Positive**: Local verification remains lightweight, zero-dependency, and fully functional offline for developer feedback and drift detection.
- **Negative / Migration**: Legacy `evidence.json` files with static HMAC signatures are classified as `LEGACY_UNATTESTED` and rejected by release/stabilization gates unless explicitly overridden for advisory use.
