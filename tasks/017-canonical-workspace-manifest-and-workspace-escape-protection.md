---
type: Task Package
title: 'Task 017: Canonical Workspace Manifest & Workspace-Escape Protection'
description: 'Deterministisk SHA-256 kildemanifest, POSIX rettigheds-bit, symlink flugt-beskyttelse, præ/post testdrift-detektion og fuld offline non-git understøttelse'
status: stable
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-25T15:39:00Z'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-08-25T16:03:36Z'
tags:
- manifest
- source-state
- workspace-escape
- security
- okf
sources:
- id: adr-0005
  resource: docs/adr/0005-two-tier-verification-and-attestation-model.md
  title: 'ADR 0005: Two-Tier Evidence and Trust Boundary Model'
---

# Task 017: Canonical Workspace Manifest & Workspace-Escape Protection

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-25`  

## 🎯 Formål
Etablere en deterministisk, platformssikker kildemanifest-beregning i overensstemmelse med ADR 0005:
1. Konfigurerbare kildescopes fra `gauntlet.toml` med standard fallback (`src`, `tests`, `tools`, `plugins`, `spec.md`, `README.md`, `pyproject.toml`).
2. Deterministisk serialisering af manifest: leksikografisk sorterede UTF-8 linjer `<sha256> <mode> <normalized_path>\n`.
3. Sikker håndtering af symlinks: følg ikke symlinks internt, men beregn digest af symlink-target og afvis symlinks, der peger uden for workspace-roden (`WorkspaceEscapeError`).
4. Dobbelt digest: `source_manifest_digest_pre` og `source_manifest_digest_post` for at opdage test-inducerede mutationer og parallel kildedrift.
5. Særskilt beregning af `config_digest`, `task_digest` og `policy_digest`.
6. Fuld understøttelse af offline miljøer uden `.git` eller `git` binærfil.

## 📋 Acceptance Criteria
- [x] Implementere `CanonicalWorkspaceManifest` i `src/agent_gauntlet/features/evidence/source_state.py`.
- [x] Implementere symlink-tjek der fejler med `WorkspaceEscapeError`, hvis et symlink peger uden for workspace.
- [x] Beregne pre- og post-verifikations kildedigests omkring gauntlet-kørslen og rapportere fejl, hvis kildekoden ændres under test.
- [x] Beregne særskilte digests for opgaver, konfiguration og politiker.
- [x] Tilføje property- og invariant-tests for determinisme, POSIX mode-ændringer, Unicode normalisering og non-git kørsel.

## 🚫 Must NOT
- Må IKKE tillade path traversal eller workspace-flugt via symlinks.
- Må IKKE inkludere flygtige cachemapper (`.venv`, `__pycache__`, `.pytest_cache`, `.hypothesis` osv.) eller genererede evidensfiler i manifestet.

## 📝 Revisions
- 2026-08-25: Oprettet iht. godkendt arkitekturplan for Two-Tier Evidence Model (P0).

## 🧪 Verifikation
- `PYTHONPATH=src /usr/bin/python3 -m unittest tests/features/test_gauntlet_properties.py`
- `PYTHONPATH=src /usr/bin/python3 -m unittest discover tests`
