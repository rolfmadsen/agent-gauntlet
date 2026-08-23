---
type: Task Package
title: 'Task 009: Antigravity Adapter & Plugin Layer'
status: stable
tags:
- task
- gauntlet
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-23T11:00:00Z'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-08-23T11:30:00Z'
---

# Task 009: Google Antigravity Adapter & Formal Plugin Architecture

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-23`  

## 🎯 Formål
Formalisere og færdiggøre adapter- og plugin-arkitekturen specifikt for **Google Antigravity IDE**, så:
1. Antigravity-specifikke payloads, tool-kald og hook-definitioner isoleres i et dedikeret adapterlag (`src/agent_gauntlet/features/adapters/antigravity/`).
2. Plugin-strukturen i `plugins/agent-gauntlet/` (manifest, hooks, bundled skills) kan valideres mekanisk.
3. `scaffolder.py` og `cli.py` understøtter eksplicit harness-valg med `antigravity` som fuldt implementeret standard.
4. Alle snitflader er dækket af sort-boks enhedstests og 100% mutation testing.

## 📋 Acceptance Criteria
- [x] Oprette `src/agent_gauntlet/features/adapters/antigravity/` med:
  - Adapter til deserialisering og normalisering af Antigravity PreInvocation payloads (`tool_name`, `tool_input` for `run_command`, `write_to_file`, `replace_file_content`, `multi_replace_file_content`).
  - Bridge til den centrale `evaluate_tool_invocation` gatekeeper-motor.
- [x] Oprette en `validate_plugin()` funktion i adapterlaget, som mekanisk validerer:
  - `plugins/agent-gauntlet/plugin.json` (korrekt format, eksisterende skills og gyldige entrypoints).
  - `plugins/agent-gauntlet/hooks.json` (gyldig `pre_tool_invocation` kommando).
  - Bundled skills i `plugins/agent-gauntlet/skills/` (`old-coder`, `grill-me`, `grill-with-docs`, `diagnose`).
- [x] Opdatere `scaffolder.py` og `agent-gauntlet init` til at acceptere `--harness` flag (med `antigravity` som default).
- [x] Oprette omfattende sort-boks enhedstests i `tests/features/test_adapter_antigravity.py`.
- [x] Tilføje mutationsmutanter i `tools/mutants.py` der sikrer 100% kill-ratio på adapterlogikken.
- [x] `agent-gauntlet verify --task-id 009-antigravity-adapter-and-plugin-layer` består og udskriver grøn evidens.

## 🚫 Must NOT
- Må IKKE indføre afhængigheder fra den harness-agnostiske kerne (`features/gauntlet/`, `features/evidence/`, `features/diagnostics/`) mod Antigravity adapteren (afhængigheden må kun gå fra adapter -> kerne).
- Må IKKE bryde bagudkompatibiliteten for det eksisterende `agent_gauntlet.features.hooks.gatekeeper` CLI-hook entrypoint.
- Må IKKE foretage eksterne netværkskald eller remote git-operationer.

## 📝 Revisions
- 2026-08-23: Oprettet som Førsteprioritets-opgave ifm. multi-harness adapter-arkitektur ifølge ROADMAP.md.
- 2026-08-23: Fuldført som Vertical Slice Adapter med 100% test-pass og 28/28 mutants dræbt (100% kill ratio).

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `PYTHONPATH=src python3 tools/mutants.py`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli verify --task-id 009-antigravity-adapter-and-plugin-layer`
