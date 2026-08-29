---
type: Task Package
title: 'Task 025: Integrate Code-Review Skill and Verification Phase Wiring'
description: 'Integration af Matt Pococks to-aksede code-review skill i agent-gauntlet, scaffolding og review-fase handoffs.'
status: draft
tags:
- task
- skills
- code-review
- gauntlet
- handoff
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-29T09:54:00Z'
---

# Task 025: Integrate Code-Review Skill and Verification Phase Wiring

**Status**: `DONE`  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-29`  
**Fuldført**: `2026-08-29`  

## 🎯 Formål
Integrere Matt Pococks to-aksede `code-review` skill (Standards vs Spec med Fowler code smells baseline) som en officiel bundlet skill i `agent-gauntlet`, registrere den i plugin-manifestet, sikre at den automatisk inkluderes i nyskabte projekter via scaffolderen, samt koble den direkte ind i den uafhængige kode-granskningsfase (`Senior Software Engineer (Independent Code Review & Audit)`).

## 📋 Acceptance Criteria
- [x] Oprette `.agents/skills/code-review/SKILL.md` og `plugins/agent-gauntlet/skills/code-review/SKILL.md` med fuld specifikation for to-akset review (Standards vs Spec) og Fowler code smells baseline.
- [x] Registrere `"code-review"` i `plugins/agent-gauntlet/plugin.json` under `skills`.
- [x] Tilføje `SKILL_CODE_REVIEW` konstant og registrere `.agents/skills/code-review/SKILL.md` i `skills_map` og `DEFAULT_AGENTS_MD` i `src/agent_gauntlet/features/scaffold/scaffolder.py`.
- [x] Opdatere `.agents/AGENTS.md` med `code-review` under Bundled Agent Skills samt opdatere intent-klassificering for review/audit.
- [x] Opdatere `infer_next_session_role()` i `src/agent_gauntlet/features/evidence/verifier.py` til eksplicit at instruere audit-rollen (`Senior Software Engineer (Independent Code Review & Audit)`) i at anvende `code-review` skillen til to-akset validering.
- [x] Oprette `skills/engineering-code-review/SKILL.md` i det globale `mattpocock-skills-plugin`.
- [x] Opdatere enhedstests i `tests/features/test_scaffold.py` og `tests/features/test_evidence.py` for at verificere scaffolding og handoff-prompts.
- [x] `agent-gauntlet validate-plugin` godkender plugin-strukturen uden fejl eller advarsler.
- [x] 100% test pass rate i `tests/` og 100% mutation kill-rate i `tools/mutants.py`.

## 🚫 Must NOT
- Må IKKE bryde eksisterende standard-skills (`old-coder`, `grill-me`, `grill-with-docs`, `diagnose`).
- Må IKKE ændre eksisterende CLI interfaces eller ødelægge plugin-manifest schemaet.
- Må IKKE hardcode uunderstøttede afhængigheder eller eksterne netværkskald.

## 📝 Revisions
- 2026-08-29: Oprettet efter brugergodkendelse af implementeringsplanen for integrering af Matt Pococks `code-review` skill.
- 2026-08-29: Fuldført med alle 180 enhedstests og 46/46 mutanter killed (100%).

## 🧪 Verifikation
- `PYTHONPATH=src python3 -m unittest discover tests`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli validate-plugin -p plugins/agent-gauntlet`
- `PYTHONPATH=src python3 tools/mutants.py`
- `PYTHONPATH=src python3 -m agent_gauntlet.cli verify --task-id 025-integrate-code-review-skill`
