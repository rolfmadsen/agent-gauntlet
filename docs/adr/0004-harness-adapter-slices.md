---
type: Architectural Decision Record
title: 'ADR 0004: Harness Adapter Slices'
status: stable
tags:
- architecture
- adr
generated:
  by: human:maintainer
  at: '2026-08-23T10:00:00Z'
verified:
- by: human:maintainer
  at: '2026-08-23T10:00:00Z'
---

# 4. Vertical Slice Harness Adapters

**Status**: `accepted`  
**Date**: `2026-08-23`  

## Context
Forskellige AI-agenter og harnesses (Google Antigravity IDE, Claude Code, DeepSeek/OpenHands osv.) anvender vidt forskellige mekanismer til tool-interception, lifecycle hooks, manifest-filer og diagnostik-formater.
Tidligere overvejede vi et tungt, flerlags Hexagonal/Ports & Adapters abstractions-lag. Dette ville dog introducere unødig kobling og bryde med `agent-gauntlet`'s etablerede Package-by-Feature princip (ADR 0001).

## Decision
1. Hver harness-integration implementeres som en **selvstændig, autonom vertikal feature-slice** under `src/agent_gauntlet/features/adapters/<harness>/`.
2. Slices deler udelukkende enkle, harness-agnostiske datastrukturer (`NormalizedToolCall`, `ToolActionType`, `ValidationResult`) fra `src/agent_gauntlet/features/adapters/models.py`.
3. Kernens øvrige slices (`gauntlet/`, `evidence/`, `diagnostics/`, `stacks/`, `config/`) forbliver 100% uafhængige af adapterne.
4. Hver adapter varetager normalisering af platformens rå tool-kald, afvikling af gatekeeper-regler, mekanisk validering af platformens plugin-manifest/hooks samt platformsspecifikke entrypoints.

## Consequences
- Tilføjelse af nye harnesses (f.eks. `claude_code` eller `deepseek`) sker ved at tilføje en ny, isoleret feature-pakke uden at røre ved eksisterende adapters eller kernens motor.
- Hver adapter kan testes isoleret med egne sort-boks enhedstests og mutations-mutanter.
