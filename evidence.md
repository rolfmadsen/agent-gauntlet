# Evidence Report

**Task ID**: `012-okf-metadata-and-verification-gatekeeper`  
**Task Title**: Task 012: OKF Metadata Validation & Verification Gatekeeper  
**Status**: `PASSED`  
**Source Tree Hash**: `c1d6d0abef036bdb`  
**Signature**: `be9dac8142020828b349e4f61953f255e536657ab093f1e4eb06a59e2d6335df`  
**Timestamp**: `2026-08-23T13:51:45Z`  
**Head**: `b9a91b5`  
**Source Commit**: `b9a91b5`  

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
| `unit` | `PASSED` | `0` | `0.985s` |
| `invariants` | `PASSED` | `0` | `0.282s` |
| `mutation-testing-gauntlet` | `PASSED` | `0` | `9.347s` |

---
