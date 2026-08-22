# Specification: agent-gauntlet Multi-Stack Verification & Actionable Diagnostics

## Philosophy & Core Principles
1. **Uncle Bob (Robert C. Martin) Clean Architecture & TDD:**
   - Strict Red -> Green -> Refactor cycle.
   - Transformation Priority Premise (TPP).
   - Single Responsibility Principle (SRP), Package-by-Feature (Screaming Architecture).
2. **Deterministic Cryptographic Evidence:**
   - Deterministic SHA-256 tree hashing.
   - HMAC-SHA256 signed evidence ledger (`evidence.json` and `evidence.md`).
3. **Actionable Diagnostics Engine:**
   - Structured parsing for Linters (Ruff, ESLint, Clippy), Type Checkers (Pyright, Mypy, tsc, cargo-check), Test Runners (pytest, unittest, vitest, cargo-test), Invariants (Hypothesis, fast-check, proptest), and Mutation Testing (mutants.py, Stryker, cargo-mutants).
   - Rich LLM remediation hints and location reporting.

---

## Features & Package-by-Feature Structure

```text
src/agent_gauntlet/
├── __init__.py
├── cli.py
└── features/
    ├── gauntlet/                 # Afvikling af lag, timing, fail-fast / fail-closed
    ├── evidence/                 # HMAC-SHA256, tree-hash, evidence.json / evidence.md
    ├── stacks/                   # Stack-detektion & standardprofiler (Python, TS, Rust)
    ├── diagnostics/              # Actionable LLM feedback engine & extractors
    └── config/                   # gauntlet.toml / gauntlet.json indlæsning
```

---

## Verification Criteria
- [x] 100% test pass rate across all feature suites (`tests/features/` & `tests/`).
- [x] Zero mutation survivors across core features and CLI logic (`tools/mutants.py`).
- [x] 100% kill ratio across all synthetic mutants (18/18).
- [x] Negative controls proving that invalid/tampered evidence signatures and drifted source trees are rejected.