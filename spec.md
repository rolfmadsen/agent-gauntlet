---
type: System Specification
title: "agent-gauntlet Multi-Stack Verification & Actionable Diagnostics"
description: "Makro system-specifikation, arkitektur-invarianter og verifikationskontrakter for agent-gauntlet"
status: stable
generated: { by: antigravity/gemini-3.7-flash, at: 2026-08-23T13:25:00Z }
tags: [specification, architecture, gauntlet, okf, verification]
---

# Specification: agent-gauntlet Multi-Stack Verification & Actionable Diagnostics

## Philosophy & Core Principles
1. **Uncle Bob (Robert C. Martin) Clean Architecture & TDD:**
   - Strict Red -> Green -> Refactor cycle.
   - Transformation Priority Premise (TPP).
   - Single Responsibility Principle (SRP), Package-by-Feature (Screaming Architecture).
2. **Two-Tier Evidence & Trust Boundary Model:**
   - Deterministic canonical workspace manifest and SHA-256 tree hashing with symlink workspace-escape prevention.
   - Unsigned verification reports (`verification-report.json`) for local fast feedback, drift detection, and cooperative Stop/Go gating.
   - Detached, keyless OIDC CI attestations (`attestation.bundle` / Sigstore / in-toto) produced strictly in privileged post-merge/release workflows.
   - Orthogonal evaluation dimensions (`verification_result`, `attestation_status`, `trust_decision`).
3. **Actionable Diagnostics Engine:**
   - Structured parsing for Linters (Ruff, ESLint, Clippy), Type Checkers (Pyright, Mypy, tsc, cargo-check), Test Runners (pytest, unittest, vitest, cargo-test), Invariants (Hypothesis, fast-check, proptest), and Mutation Testing (mutants.py, Stryker, cargo-mutants).
   - Rich LLM remediation hints and location reporting.
4. **Standardized Knowledge Metadata & Gatekeeping (OKF v0.2):**
   - Strict frontmatter schema, ISO 8601 UTC timestamps, temporal invariants ($t_{verified} \ge t_{generated}$), and actor enforcement (`human:<id>`, `<agent>/<ver>`, `process:<id>`).

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
    └── okf/                      # OKF v0.2 metadata parsing, validation, tidsinvarianter & stempling
```


---

## Verification Criteria
- [ ] 100% test pass rate across all feature suites (`tests/features/` & `tests/`).
- [ ] Zero mutation survivors across core features, adapter slices, and CLI logic (`tools/mutants.py`).
- [ ] 100% kill ratio across all synthetic mutants.
- [ ] Negative controls proving that invalid/tampered evidence signatures and drifted source trees are rejected.
- [ ] Automated mechanical validation of adapter plugins, skills, and lifecycle hooks via `agent-gauntlet validate-plugin`.
- [ ] Automated mechanical validation of OKF v0.2 frontmatter across all repository documentation via `agent-gauntlet okf validate`.