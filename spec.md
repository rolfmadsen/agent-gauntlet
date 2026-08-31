---
type: System Specification
title: "agent-gauntlet Multi-Stack Verification & Actionable Diagnostics"
description: "Makro system-specifikation, arkitektur-invarianter og verifikationskontrakter for agent-gauntlet"
status: stable
generated: { by: antigravity/gemini-3.7-flash, at: 2026-08-30T09:17:00Z }
tags: [specification, architecture, gauntlet, okf, verification, supervisor, wasm]
---

# Specification: agent-gauntlet Multi-Stack Verification & Actionable Diagnostics

## Philosophy & Core Principles
1. **Uncle Bob (Robert C. Martin) Clean Architecture & TDD:**
   - Strict Red -> Green -> Refactor cycle.
   - Transformation Priority Premise (TPP).
   - Single Responsibility Principle (SRP), Package-by-Feature (Screaming Architecture).
2. **Three-Tier Evidence & Trust Boundary Model:**
   - Deterministic canonical workspace manifest and SHA-256 tree hashing with symlink workspace-escape prevention.
   - `LOCAL_UNSUPERVISED`: Fast feedback unsigned report for cooperative drift detection and Stop/Go gating.
   - `LOCAL_SUPERVISED`: Signed local verification report issued by a privilege-separated supervisor with ephemeral task certificates and hash-chained session logs.
   - `CI_ATTESTED`: Detached, keyless OIDC CI attestations (`attestation.bundle` / Sigstore / in-toto) produced strictly in privileged post-merge/release workflows.
   - Orthogonal evaluation dimensions (`verification_result`, `attestation_status`, `trust_decision`).
3. **Local Supervisor & Embedded WASM Verifier:**
   - Zero ambient authority WebAssembly policy component (`wit/gauntlet_policy.wit`) for deterministic capability evaluation.
   - Privilege separation: task private keys and installation identity held exclusively by the supervisor with strict OS permissions (`0700`/`0600`) outside the workspace.
   - Unprivileged Linux sandbox runner (`BubblewrapSandboxRunner`) for frozen workspace verification.
   - On-demand systemd socket activation for transparent developer experience without persistent background processes.
4. **Actionable Diagnostics Engine:**
   - Structured parsing for Linters (Ruff, ESLint, Clippy), Type Checkers (Pyright, Mypy, tsc, cargo-check), Test Runners (pytest, unittest, vitest, cargo-test), Invariants (Hypothesis, fast-check, proptest), and Mutation Testing (mutants.py, Stryker, cargo-mutants).
   - Rich LLM remediation hints and location reporting.
5. **Standardized Knowledge Metadata & Gatekeeping (OKF v0.2):**
   - Strict frontmatter schema, ISO 8601 UTC timestamps, temporal invariants ($t_{verified} \ge t_{generated}$), and actor enforcement (`human:<id>`, `<agent>/<ver>`, `process:<id>`).
6. **Polyglot & Multi-Stack Scaffolding:**
   - Composable coding standards generation for multi-language workspaces (TypeScript/React + Python/Rust) with uniform section numbering and transversal boundary invariants.

---

## Features & Package-by-Feature Structure

```text
src/agent_gauntlet/
├── __init__.py
├── cli.py
└── features/
    ├── gauntlet/                 # Afvikling af lag, timing, fail-fast / fail-closed
    ├── evidence/                 # Canonical manifest, verification report, attestation & trust policy
    ├── tasks/                    # Opgavekontrakter, markdown-parsing og statussemantik
    ├── stacks/                   # Stack-detektion & standardprofiler (Python, TS, Rust)
    ├── diagnostics/              # Actionable LLM feedback engine & extractors
    ├── config/                   # gauntlet.toml / gauntlet.json indlæsning
    ├── scaffold/                 # Projekt-initialisering & skabeloner
    ├── hooks/                    # Bagudkompatible gatekeeper hooks
    ├── adapters/                 # Vertikale feature-slices for AI-harnesses (Google Antigravity mv.)
    ├── supervisor/               # Lokal privilege-separated supervisor, FSM, event log & platform seams
    │   ├── core/                 # Portabel forretningslogik, FSM, modeller, snapshot, seams
    │   ├── wasm/                 # WebAssembly component verifier & host integration
    │   └── platform/linux/       # Linux-specifik systemd, Unix socket, bubblewrap & key provider
    ├── okf/                      # OKF v0.2 metadata parsing, validation, tidsinvarianter & stempling
    └── doctor/                   # Read-only integritets- og dublet-scanner samt AI migration prompt generator
```

---

## 🚫 Must NOT (System & Business Invariants)
1. **Zero Uncontrolled Writes**: An agent must NEVER be granted write access to `src/` or `tests/` without an approved, active task containing explicit `Must NOT` invariants.
2. **Strict Trust Boundary**: A `LOCAL_UNSUPERVISED` report must NEVER be declared `release_eligible: true` under default trust policy without a valid, independent CI attestation bundle.
3. **Zero Drift Tolerance**: Any single-byte or mode change in the workspace after verification MUST invalidate evidence records as `Source Drift`.
4. **Temporal Integrity**: An OKF document must NEVER have $t_{verified} < t_{generated}$ or timestamps beyond clock skew tolerance in the future.
5. **Zero Ambient Authority**: WASM policy verification must execute with pure in-memory state and zero ambient filesystem or network host bindings.
6. **Slim Dispatcher Contract**: `src/agent_gauntlet/cli.py` must remain a slim command dispatcher strictly under 300 lines.

---

## Verification Criteria
- [ ] 100% test pass rate across all feature suites (`tests/features/` & `tests/`).
- [ ] Zero mutation survivors across core features, adapter slices, and CLI logic (`tools/mutants.py`).
- [ ] 100% kill ratio across all synthetic mutants.
- [ ] Negative controls proving that invalid/tampered evidence signatures and drifted source trees are rejected.
- [ ] Automated mechanical validation of adapter plugins, skills, and lifecycle hooks via `agent-gauntlet validate-plugin`.
- [ ] Automated mechanical validation of OKF v0.2 frontmatter across all repository documentation via `agent-gauntlet okf validate`.
- [ ] Automated mechanical validation of release readiness and documentation synchronization via `agent-gauntlet check-release`.
- [ ] Automated mechanical validation of task specifications and business rules via `agent-gauntlet check-spec`.
- [ ] Automated mechanical workspace integrity and orphan/duplicate diagnostics via `agent-gauntlet doctor`.