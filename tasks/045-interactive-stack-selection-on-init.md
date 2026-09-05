---
type: Task Package
title: 'Task 045: Interactive Stack Selection on Init in Empty Workspaces'
description: 'Interaktiv forespørgsel ("Hvilken primær stack bygger du på?") under agent-gauntlet init / scaffold i tomme projekter uden automatisk detekteret tech stack.'
status: stable
tags:
- task
- scaffold
- init
- interactive
- cli
- onboarding
generated:
  by: antigravity/gemini-3.8-flash
  at: '2026-09-05T12:43:00Z'
verified:
- by: process:agent-gauntlet-verify
  at: '2026-09-05T15:08:00Z'
---

# Task 045: Interactive Stack Selection on Init in Empty Workspaces

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-09-05`  
**Fuldført**: `2026-09-05`  

## 🎯 Formål
Forbedre onboarding- og initialiseringsoplevelsen, når `agent-gauntlet init` eller `scaffold` afvikles i et tomt repository eller et projekt uden genkendelige stack-manifestfiler:
1. **Interaktiv Prompt ved Ubestemt Stak**: Hvis `detect_stacks(workspace)` returnerer en tom liste (intet fund af `pyproject.toml`, `package.json`, `Cargo.toml` mv.), og brugeren ikke eksplicit har angivet `--stack` / `-s`, skal systemet under en interaktiv TTY-session prompte brugeren:
   `"Hvilken primær stack bygger du på?"`
2. **Valgmuligheder & Normalisering**: Præsentere de understøttede stacks (`python`, `typescript`, `rust`) med mulighed for valg via tal eller navn, samt en markeret standard/anbefalet default (f.eks. `python`).
3. **Headless & Script-sikkerhed**: Sikre at non-interaktive miljøer (CI/CD, pipes, `sys.stdin.isatty() == False`, eller `--no-input` flag) ikke blokerer eller hænger, men enten anvender en deterministisk default eller fejler informativt.
4. **Scaffolding Integration**: Det valgte stak-navn føres direkte til `ProjectScaffolder` og danner relevante konfigurationsfiler (`gauntlet.toml`, `spec.md`, `CODING_STANDARDS.md` etc.).

## 📋 Acceptance Criteria
- [x] **Interaktiv Spørgesession i CLI (`cli.py` / `scaffolder.py`)**:
  - [x] Når `detect_stacks(workspace)` ikke finder nogen stak, og hverken `--stack` eller `--stacks` er angivet på kommandolinjen:
    - [x] Kontroller om stdin er en interaktiv TTY (`sys.stdin.isatty()`).
    - [x] Prompt brugeren: `"Hvilken primær stack bygger du på?"` med overskuelige valgmuligheder (f.eks. `[1] Python (default)`, `[2] TypeScript`, `[3] Rust`).
    - [x] Valider brugerens input mod `SUPPORTED_STACKS` (`python`, `typescript`, `rust`). Hvis ugyldigt input tastes, gives en venlig fejlbesked, og der spørges igen (eller afbrydes sikkert).
    - [x] Tryk på Enter uden input vælger den markerede standardstak.
- [x] **Non-Interaktiv Kørsel & Flag-Overstyring**:
  - [x] Hvis `--stack <navn>` eller `-s <navn>` er angivet, stilles der INGEN interaktive spørgsmål, og den specificerede stak anvendes direkte.
  - [x] Hvis sessionen ikke er interaktiv (`not sys.stdin.isatty()`) eller et `--no-input` flag er sat, stilles der INGEN spørgsmål. Systemet anvender standardstakken (`python`) med en orienterende advarselsmeddelelse.
- [x] **Eksisterende Stak-Autodetektion Bevares**:
  - [x] Hvis `detect_stacks(workspace)` finder én eller flere stakke i forvejen (f.eks. i et eksisterende projekt), stilles der INGEN spørgsmål, og de detekterede stakke anvendes automatisk.
- [x] **Dobbelt-Træ Konsistens**:
  - [x] Eventuelle ændringer i CLI og scaffolding-moduler synkroniseres til både `src/agent_gauntlet/` og `packages/agent-gauntlet/src/`.
- [x] **Automatiserede Enhedstests (`tests/test_cli.py` / `tests/features/test_scaffold.py`)**:
  - [x] Test med mock af interaktivt input (`builtins.input` / `sys.stdin`), der beviser, at valg af `typescript` initialiserer et TypeScript-projekt med tilhørende `gauntlet.toml`.
  - [x] Test der beviser, at `--stack` flaget omgår den interaktive prompt.
  - [x] Test der beviser, at eksisterende projektfiler omgår prompten via autodetektion.
  - [x] Test der beviser, at non-interaktiv stdin (`isatty() == False`) ikke blokerer processen.
- [x] **Gauntlet & Spec Validering**:
  - [x] `agent-gauntlet check-spec -t 045` validerer task-pakkens format og invariante regler uden fejl.
  - [x] `sh tools/gauntlet.sh` passerer 100% når opgaven implementeres.

## 🚫 Must NOT
- Må IKKE blokere eller fryse CI/CD pipelines, headless scripts eller ikke-interaktive pipes (skal altid tjekke `isatty` før `input()`).
- Må IKKE spørge brugeren interaktivt, hvis stakken allerede detekteres automatisk af `detect_stacks`.
- Må IKKE spørge brugeren interaktivt, hvis `--stack` / `-s` er angivet på kommandolinjen.
- Må IKKE crashe ved `EOFError` eller `KeyboardInterrupt` (Ctrl+C), men håndtere afbrydelse pænt med en ren afslutningsstatus.

## 📝 Revisions
- 2026-09-05: Oprettet som planlagt taskpakke forud for implementering for at optimere onboarding i tomme projekter.
- 2026-09-05: Implementeret interaktiv stack selection prompt med support for polyglot komma-valg, stderr advisory og --no-input i tomme projekter. Fuld gauntlet verifikation bestået.

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m agent_gauntlet.cli check-spec -t 045`
- `PYTHONPATH=src python3 -m unittest discover tests`
- `sh tools/gauntlet.sh`
