# Evidence Report

**Task ID**: `012-okf-metadata-and-verification-gatekeeper`  
**Task Title**: Task 012: OKF Metadata Validation & Verification Gatekeeper  
**Status**: `PASSED`  
**Source Tree Hash**: `05fbba2ef4df2507`  
**Signature**: `54098c593a81aa996722615773afed0d33f72d910964093d95c0898cfd746a89`  
**Timestamp**: `2026-08-23T13:54:43Z`  
**Head**: `c023072`  
**Source Commit**: `c023072`  

## Acceptance Criteria

- [x] Oprette `src/agent_gauntlet/features/okf/` med `models.py`, `validator.py` og `stamper.py`.
- [x] Implementere validering af:
- [x] Tilføje `okf` CLI underkommandoer (`validate` og `stamp`) i `src/agent_gauntlet/cli.py`.
- [x] Opdatere `scaffolder.py` til at generere tasks, ADRs, specs og AGENTS.md med gyldigt OKF frontmatter.
- [x] Opdatere eksisterende `.md` filer i projektet (`tasks/`, `docs/adr/`, `spec.md`, `CONTEXT.md`) til 100% valid OKF frontmatter.
- [x] Skrive unit tests i `tests/features/test_okf.py` og tilføje mutation-tests i `tools/mutants.py`.
- [x] Køre `tools/gauntlet.sh` og opnå 100% grøn verifikation og forseglet evidens.

---

## Verification Checks

| Check Name | Status | Exit Code | Duration (s) |
|---|---|---|---|
| `lint` | `FAILED` | `127` | `0.000s` |
| `types` | `FAILED` | `127` | `0.000s` |
| `unit` | `PASSED` | `0` | `0.940s` |
| `invariants` | `PASSED` | `0` | `0.293s` |
| `mutation-testing-gauntlet` | `PASSED` | `0` | `9.456s` |

---
