---
type: Architectural Decision Record
title: 'ADR 0002: Cryptographic Evidence Authority'
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

# 2. Cryptographic Evidence Authority & Source State Binding

**Status**: `accepted`  
**Date**: `2026-08-22`  

## Context
AI-genereret kode og testresultater kan forfalskes, eller kildekoden kan ændres efter at testene er kørt uden at blive opdaget (kildedrift).

## Decision
`agent-gauntlet` anvender et deterministisk SHA-256 source tree digest over alle sporede kildefiler og forsegler testresultaterne i `evidence.json` med en kryptografisk HMAC-SHA256 signatur. `agent-gauntlet check-evidence` validerer signaturen mod det aktuelle kildetræ.

## Consequences
Enhver ændring i kildekoden efter en verifikation ugyldiggør beviset, indtil gauntlettet genkøres. Kildedrift tolereres ikke (Fail-Closed).
