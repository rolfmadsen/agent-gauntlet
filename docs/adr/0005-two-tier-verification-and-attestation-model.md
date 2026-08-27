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
   - `verification-report.json`: An unsigned JSON document produced by `agent-gauntlet verify`. It records verification claims, layer outcomes, diagnostic findings, pre/post source manifest digests, config/policy/task digests, and task contracts.
   - `attestation.bundle`: An optional, detached in-toto / DSSE / Sigstore attestation bundle generated strictly within a protected, privileged CI workflow. It cryptographically binds an ambient CI identity (OIDC) to the verification report and source manifest.

2. **Orthogonal Assurance Dimensions**:
   Consumers MUST evaluate verification and trust across three independent dimensions:
   - `verification_result`: `PASSED` | `FAILED` | `ERROR` | `INCOMPLETE` | `SKIPPED`
   - `attestation_status`: `ABSENT` | `VALID` | `INVALID`
   - `trust_decision`: `ACCEPTED` | `POLICY_REJECTED`
   
   Release eligibility is strictly:
   `verification_result == PASSED AND attestation_status == VALID AND trust_decision == ACCEPTED`

3. **Canonical Workspace Manifest & Multi-Digest Binding**:
   Workspace state is captured via a deterministic SHA-256 tree manifest that works identically offline without Git. It incorporates UTF-8 normalized relative paths, file content hashes, POSIX executable permission bits, and strict symlink boundary checks. Verification and attestation checks fail closed on any drift across:
   - `source_manifest_digest` (source tree integrity)
   - `policy_digest` (`spec.md`, `CONTEXT.md`, `docs/adr/`, `.agents/`, `.github/`)
   - `config_digest` (`gauntlet.toml`, `pyproject.toml`)
   - `task_digest` (`tasks/*.md` active task contract integrity)

4. **Multi-CI & GitHub-Native Attestation Architecture**:
   - **Issuance**: In GitHub Actions, the privileged attestation job uses official `actions/attest` with Sigstore Fulcio OIDC certificates and Rekor transparency log. In other CI harnesses (GitLab, Cloud Build, Jenkins), standard `cosign` or `sigstore-python` is used.
   - **Cryptographic Verification**: Delegated to official, maintained verifiers (`gh attestation verify`, `sigstore-python`, or `cosign verify-blob`) with trusted roots, rather than custom homemade ASN.1/X.509 certificate parsers.
   - **Domain Policy Enforcement**: `agent-gauntlet check-attestation` / `TrustPolicyEngine` acts as an authoritative policy consumer evaluating the verified attestation claims (issuer, repository, workflow, runner environment, digests, criteria resolution).

5. **Self-Attestation Bootstrap & Candidate N Integrity**:
   A candidate release $N$ cannot define or assert its own verification truth. The CI signer job independently validates:
   - Schema version, non-empty acceptance criteria, zero unresolved criteria.
   - Non-empty check array with all mandatory checks `PASSED` (exit code 0).
   - Source commit, ref, and all digests matching `${{ github.sha }}` and workspace state.
   - Release $N$ is verified by the pinned, trusted release $N-1$ or trusted reusable workflow before signing.

## Consequences
- **Positive**: Eliminates all hardcoded keys and local HMAC secrets. Guarantees true cryptographic assurance tied to verifiable CI provenance.
- **Positive**: Uses official, battle-tested Sigstore verification tools (`gh attestation verify` / `sigstore`) without fragile homemade ASN.1 parsers.
- **Positive**: Local verification remains lightweight, zero-dependency, and fully functional offline for developer feedback and drift detection.
- **Negative / Migration**: Legacy `evidence.json` files with static HMAC signatures are classified as `LEGACY_UNATTESTED` and rejected by release/stabilization gates unless explicitly overridden for advisory use.

