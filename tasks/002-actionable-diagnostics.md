# Task 002: Actionable Diagnostics Engine & LLM Feedback

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-22`  
**Fuldført**: `2026-08-22`  

## 🎯 Formål
Implementere en parsing- og feedbackmotor, som omsætter rå stderr/stdout fra linters, typecheckere, testrunners, invariants og mutationstools til strukturerede JSON diagnoser med udbedringsforslag (`remediation_hint`) til autonome agent-loops.

## 📋 Acceptance Criteria
- [x] Domænemodeller for `DiagnosticFinding`, `DiagnosticReport` og `FindingType`.
- [x] Linter extractors: Ruff, ESLint, Clippy.
- [x] Typechecker extractors: Pyright, Mypy, tsc, cargo check.
- [x] Test extractors: pytest, unittest, vitest, cargo test.
- [x] Invariant extractors: Hypothesis, fast-check, proptest.
- [x] Mutation extractors: mutants.py, Stryker, cargo-mutants.
- [x] CLI flag `--diagnostics-json` til `agent-gauntlet verify`.

## 🧪 Verifikation
- Tests: `tests/features/test_diagnostics.py` (12 tests bestået).
- Evidens: Blevet verificeret og forseglet i `evidence.json`.
