# Verification Report

**Task ID**: `031-windsurf-cascade-adapter-and-rules-bridge`  
**Task Title**: Task 031: Windsurf Cascade Adapter and Rules Bridge  
**Verdict**: `PASSED`  
**Execution Origin**: `LOCAL`  
**Source Manifest Digest**: `97ff4d4f4ded84a5f28dd1292aeadf94c7907549da2938a2b957c7c78b60c341`  
**Timestamp**: `2026-08-30T10:05:55Z`  
**Head**: `73514e2`  
**Commit**: `73514e2`  

## Acceptance Criteria

- [x] Oprette `src/agent_gauntlet/features/adapters/windsurf/` vertical slice modul med `WindsurfAdapter` og regel-skabeloner.
- [x] Implementere scaffolding af `.windsurfrules` entrypoint-fil med autoritativ reference til `.agents/AGENTS.md`.
- [x] Udvide `scaffolder.py` og CLI `--harness windsurf` flag.
- [x] Tilføje sort-boks accepttests i `tests/features/test_adapter_windsurf.py` og `tests/test_cli.py`.
- [x] Tilføje mutation testing i `tools/mutants.py` til at beskytte Windsurf-adapter logik (100% kill-rate).
- [x] `agent-gauntlet okf validate` godkender alle oprettede og modificerede filer.

---

## Verification Checks

| Check Name | Status | Exit Code | Duration (s) |
|---|---|---|---|
| `lint` | `PASSED` | `0` | `0.034s` |
| `types` | `PASSED` | `0` | `1.696s` |
| `unit` | `PASSED` | `0` | `2.222s` |
| `invariants` | `PASSED` | `0` | `0.303s` |
| `mutation-testing-gauntlet` | `PASSED` | `0` | `30.117s` |

---
