---
type: Task Package
title: 'Task 034: NPM and NPX Distribution Wrapper'
description: 'Implementation af npm/npx distributionslag (packages/agent-gauntlet), der gør npx agent-gauntlet init muligt direkte i ethvert projekt uden forudgående installation.'
status: draft
tags:
- task
- npm
- npx
- distribution
- dx
- gauntlet
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-29T13:30:00Z'
---

# Task 034: NPM and NPX Distribution Wrapper

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-29`  

## 🎯 Formål
Etablere en ultra-lavfriktions distributionsmodel for `agent-gauntlet` via **npm / npx** (og tilsvarende `pnpm dlx` / `yarn dlx` / `bunx`), så frontend- og fullstack-udviklere kan køre `npx agent-gauntlet init` direkte i projekter som f.eks. TypeScript/React webapps uden forudgående global Python-installation eller cloning:
1. Oprette en officiel, slank npm-pakke i `packages/agent-gauntlet/` med `package.json` og et robust `bin/agent-gauntlet.js` CLI-entrypoint.
2. CLI-wrapperen skal automatisk lokalisere `python3`/`python` på værtssystemet eller anvende bundlet Python-kald, videresende samtlige CLI-argumenter, understøtte interaktive streams (stdin/stdout/stderr) og returnere de korrekte exit-koder deterministisk.
3. Klargøre npm publishing workflow i GitHub Actions CI.

## 📋 Acceptance Criteria
- [x] Oprette `packages/agent-gauntlet/package.json` med `name: "agent-gauntlet"`, `bin: { "agent-gauntlet": "./bin/agent-gauntlet.js" }` og version synkroniseret med kernen.
- [x] Implementere `packages/agent-gauntlet/bin/agent-gauntlet.js` med fail-safe Python-detektion, gennemsigtig argument-videresendelse og signal/exit-code håndtering.
- [x] Sikre at `npx agent-gauntlet init` virker fejlfrit i ethvert vilkårligt projektkatalog (f.eks. `knowledgegraphstudio`).
- [x] Tilføje automatiseret integrationstest for npx/Node-wrapperen i testsuiten (`tests/test_npx_wrapper.py` eller tilsvarende).
- [x] `agent-gauntlet okf validate` godkender alle nye metadata-filer.

## 🚫 Must NOT
- Må IKKE introducere tunge eksterne npm-afhængigheder i wrapperen (skal bruge 100% native Node.js standardmoduler som `child_process`, `fs`, `path`).
- Må IKKE maskere fejl-koder fra `agent-gauntlet.cli` (exit code skal returneres 1:1).

## 📝 Revisions
- 2026-08-29: Oprettet for at levere en friktionsfri zero-setup installationsoplevelse via npm/npx økosystemet.
- 2026-08-29: Implementeret, verificeret med 5 acceptance tests og 2 mutanter dræbt (100% kill-rate). Status sat til DONE.

## 🧪 Verifikation
- `node packages/agent-gauntlet/bin/agent-gauntlet.js --help`
- `node packages/agent-gauntlet/bin/agent-gauntlet.js init --workspace /tmp/test-npx-workspace`
- `PYTHONPATH=src python3 -m unittest discover tests`
- `sh tools/gauntlet.sh`
