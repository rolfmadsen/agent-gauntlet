# 3. Kirurgisk Pre-Invocation Gatekeeper & Ingen Remote Push

**Status**: `accepted`  
**Date**: `2026-08-22`  

## Context
Tidligere toolchain-systemer blokerede alle værktøjer globalt via tunge SQLite-databaser, hvilket lammede udviklingsflowet. Omvendt tillader uregulerede AI-agenter utilsigtede ændringer af produktionskode i blinde eller utilsigtede `git push` handlinger til remote repositories.

## Decision
1. `agent-gauntlet` anvender et letvægts, database-frit Pre-Invocation Hook, der udelukkende beskytter produktionskode i `src/` og `tests/` mod ændringer, hvis der ikke findes en aktiv task i `tasks/`.
2. Alle læseværktøjer, task-dokumenter og `CONTEXT.md` forbliver 100% frie for blokering.
3. AI-agenten må **aldrig** foretage `git push` eller publicere til remote git repositories; git-operationer er strengt lokale checkpoints.

## Consequences
AI-agenten er fysisk forhindret i at skrive kode uden en godkendt opgave, og brugerens remote repo er sikret mod utilsigtede ændringer.
