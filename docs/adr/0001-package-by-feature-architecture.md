# 1. Package-by-Feature (Screaming Architecture)

**Status**: `accepted`  
**Date**: `2026-08-22`  

## Context
Tidligere var kildekoden opdelt i flade filer eller tekniske lag. Dette gjorde koden svær at navigere, øgede utilsigtet kobling og slørede domænegrænserne.

## Decision
Al kildekode og tilhørende tests organiseres som **Package-by-Feature** under `src/agent_gauntlet/features/<feature>/` og `tests/features/<feature>/`. Hver feature er en selvstændig, høj-sammenhængende underpakke med sine egne modeller, logik og tests. Rod-filer som `cli.py` orkestrerer udelukkende feature-pakkerne.

## Consequences
Nye funktioner må ikke tilføjes som løse filer i roden, men skal placeres i en dedikeret underpakke. Teststrukturen skal spejle kildestrukturen 1:1.
