---
type: Task Package
title: 'Task 012: OKF Metadata Validation & Verification Gatekeeper'
description: Implementering af OKF v0.2 validator, CLI integration og skema-håndhævelse
  for markdown-viden
status: stable
generated:
  by: antigravity/gemini-3.7-flash
  at: 2026-08-23 13:23:00+00:00
verified:
- by: process:agent-gauntlet-verify
  at: 2026-08-23 13:37:00+00:00
- by: process:agent-gauntlet-verify
  at: '2026-08-23T13:51:45Z'
tags:
- okf
- validation
- gatekeeper
- metadata
- cli
sources:
- id: okf-spec-v02
  resource: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
  title: Open Knowledge Format (OKF) Spec v0.2
- id: adr-0002
  resource: /docs/adr/0002-cryptographic-evidence-authority.md
  title: 'ADR 0002: Cryptographic Evidence Authority'
---

# Task 012: OKF Metadata Validation & Verification Gatekeeper

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-23`  

## 🎯 Formål
Implementere standardiseret understøttelse og streng validering af **Open Knowledge Format (OKF v0.2)** i `agent-gauntlet`:
1. Skabe en dedikeret `agent_gauntlet/features/okf/` pakke til parsing, validering og stempling af OKF frontmatter i Markdown-dokumenter.
2. Håndhæve strenge tids- og aktørinvarianter (ISO 8601 UTC med sekundpræcision, ingen fremtidsstempler, $t_{verified} \ge t_{generated}$, godkendte aktørpræfikser `human:`, `<agent>/<ver>`, `process:`).
3. Tilføje `agent-gauntlet okf validate` og `agent-gauntlet okf stamp` CLI-kommandoer samt integrere OKF-validering i gauntlet-verifikationsløkken.
4. Opgradere scaffolding (`scaffolder.py`) og eksisterende projektdokumenter (`tasks/`, `docs/adr/`, `spec.md`, `CONTEXT.md`) til OKF v0.2.

## 📋 Acceptance Criteria
- [x] Oprette `src/agent_gauntlet/features/okf/` med `models.py`, `validator.py` og `stamper.py`.
- [x] Implementere validering af:
  - Påkrævet `type` felt samt kendte typer (`Task Package`, `Architectural Decision Record`, `System Specification`, mv.).
  - ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ` eller explicit UTC offset).
  - Tidsmæssig invariant: Ingen stempler længere end 60 sekunder i fremtiden.
  - Tidsmæssig invariant: `verified.at >= generated.at`.
  - Aktør-formater: `human:<id>`, `<agent>/<version>`, `process:<id>`.
  - Status: `draft | stable | deprecated`.
- [x] Tilføje `okf` CLI underkommandoer (`validate` og `stamp`) i `src/agent_gauntlet/cli.py`.
- [x] Opdatere `scaffolder.py` til at generere tasks, ADRs, specs og AGENTS.md med gyldigt OKF frontmatter.
- [x] Opdatere eksisterende `.md` filer i projektet (`tasks/`, `docs/adr/`, `spec.md`, `CONTEXT.md`) til 100% valid OKF frontmatter.
- [x] Skrive unit tests i `tests/features/test_okf.py` og tilføje mutation-tests i `tools/mutants.py`.
- [x] Køre `tools/gauntlet.sh` og opnå 100% grøn verifikation og forseglet evidens.

## 🚫 Must NOT
- Må IKKE introducere tunge eksterne afhængigheder (anvend standardbiblioteket eller eksisterende pakkeafhængigheder).
- Må IKKE fejle uhåndteret på markdown-filer uden frontmatter, hvis de ikke er en del af den overvågede dokumentskare.
- Må IKKE tillade syntetiske / ugyldige ISO-stempler.

## 📝 Revisions
- 2026-08-23: Oprettet efter arkitektursparring om OKF spec v0.2 integration.
- 2026-08-23: Fuld implementering af `features/okf/`, CLI subcommands, 33/33 mutanter killed og forseglet evidens.

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `python3 tools/mutants.py`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli okf validate`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli verify --task-id 012-okf-metadata-and-verification-gatekeeper`

