# Task 005: Sikker, Ikke-Destruktiv Projekt-Scaffolding & Afinstallations-Guide

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-22`  
**Fuldført**: `2026-08-22`  

## 🎯 Formål
Gøre `agent-gauntlet init` i stand til at klargøre et komplet, AI-sikkert Evidence-First workspace i et nyt eller eksisterende projekt uden at overskrive brugerens eksisterende filer (`CONTEXT.md`, `tasks/`, `docs/adr/`, `.agents/`, `gauntlet.toml`), samt dokumentere alle oprettede artefakter og en transparent afinstallationsprocedure i `README.md`.

## 📋 Acceptance Criteria
- [x] Implementere `src/agent_gauntlet/features/scaffold/scaffolder.py`, der struktureret opretter:
  - `gauntlet.toml` (eller `.json`) tilpasset den detekterede stack.
  - `CONTEXT.md` med Aristoteles-formel starter-glossary.
  - `tasks/` med `001-bootstrap.md`.
  - `docs/adr/` med `README.md` og `0001-initial-architecture.md`.
  - `.agents/AGENTS.md` med transparent Response HUD og task-retningslinjer.
  - `.agents/hooks.json` med PreInvocation gatekeeper-konfiguration.
  - `.agents/skills/` med de 4 bundled skills (`old-coder`, `grill-me`, `grill-with-docs`, `diagnose`).
- [x] Hver eneste fil og mappe skal tjekkes for eksistens: Eksisterende filer må **aldrig** overskrives, medmindre `--force` eksplicit er angivet.
- [x] Logge detaljeret status for hver fil (`[CREATED]`, `[EXISTS/SKIPPED]`, `[OVERWRITTEN]`).
- [x] Opdatere `agent-gauntlet init` i `src/agent_gauntlet/cli.py` til at anvende scaffolderen med `--force` og `--format` flag.
- [x] Opdatere `README.md` med et komplet manifest over oprettede filer og en sikker one-line afinstallationskommando (`rm -rf ...`).
- [x] Skrive sort-boks tests i `tests/features/test_scaffold.py` og `tests/test_cli.py`.
- [x] Dræbe 100% af mutanter i `tools/mutants.py` og bestå hele 5-lags gauntletten.

## 🚫 Must NOT
- Må IKKE overskrive eksisterende kode eller konfiguration uden eksplicit `--force`.
- Må IKKE ændre eller slette filer uden for projekt-roden.
- Må IKKE fejle hvis delvise mapper (f.eks. en eksisterende `docs/` eller `.agents/`) allerede eksisterer.

## 📝 Revisions
- 2026-08-22: Oprettet og gennemført efter brugeranmodning om automatisk scaffolding til nye projekter med zero-lockin afinstallation.

## 🧪 Verifikation
- Unit & Acceptance: `PYTHONPATH=src python3 -m unittest discover tests` (66 tests bestået)
- Gauntlet script: `sh tools/gauntlet.sh` (5/5 lag bestået, 23/23 mutanter dræbt)
- Evidence check: `PYTHONPATH=src python3 -m agent_gauntlet.cli verify --task-id 005-safe-project-scaffolding` ([VALID])
