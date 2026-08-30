---
type: Task Package
title: 'Task 036: macOS launchd Service and Seatbelt Sandbox Platform Seam'
description: 'Udvidelse af supervisorarkitekturen til macOS med launchd socket activation og sandbox-exec/seatbelt isolation.'
status: draft
tags:
- task
- macos
- launchd
- seatbelt
- sandbox
- supervisor
- future
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-30T09:07:00Z'
---

# Task 036: macOS launchd Service and Seatbelt Sandbox Platform Seam

**Status**: `DRAFT` (Planlagt til fremtidig release)  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-30`  

## 🎯 Formål
Tilføje fuld native platformunderstøttelse for **macOS** til `agent-gauntlet`'s lokale supervisorarkitektur, så udviklere på macOS (Apple Silicon og Intel) opnår samme friktionsfri, privilegie-adskilte `LOCAL_SUPERVISED` oplevelse som på Linux:
1. Implementere `LaunchdServiceManager` under `ServiceManagerSeam` ved hjælp af `launchd.plist` socket activation (`Sockets` dictionary og `launch_activate_socket`).
2. Implementere `SeatbeltSandboxRunner` under `SandboxRunnerSeam` ved hjælp af macOS `sandbox-exec` og Seatbelt-profiler (`(deny default) (allow process-exec ...)`).
3. Opsætte dedikeret macOS GitHub Actions CI-matrix runner til empirisk E2E-verifikation.

## 📋 Acceptance Criteria
- [ ] Implementere `LaunchdServiceManager` i supervisor bootstrapperen, som kan installere og fjerne `~/Library/LaunchAgents/dev.agent-gauntlet.supervisor.plist`.
- [ ] Understøtte on-demand socket activation via macOS `launchd` uden manuel dæmon-start.
- [ ] Implementere `SeatbeltSandboxRunner`, der afvikler checks i en isoleret proces uden netværksadgang mod et frosset workspace-snapshot.
- [ ] Tilføje macOS GitHub Actions test-job i `.github/workflows/ci.yml` (`macos-latest`).
- [ ] Køre fuld E2E-test på macOS og bevise, at `LOCAL_SUPERVISED` rapport genereres og verificeres fejlfrit.

## 🚫 Must NOT
- Må IKKE påstå eller markere macOS som officielt understøttet, før alle end-to-end tests kører grønt på en ægte macOS runner.
- Må IKKE bryde eksisterende Linux `systemd` eller POSIX socket implementationer.

## 📝 Revisions
- 2026-08-30: Oprettet som dedikeret opgavepakke for macOS-udvidelse efter v0.4.0 Linux-stabilisering.

## 🧪 Verifikation
- `npm run test:e2e:macos` på macOS GitHub runner.
- Verifikation af `launchd.plist` gyldighed via `plutil -lint`.
