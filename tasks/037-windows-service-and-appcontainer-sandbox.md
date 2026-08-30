---
type: Task Package
title: 'Task 037: Windows Service and AppContainer Sandbox Platform Seam'
description: 'Udvidelse af supervisorarkitekturen til Windows med Windows Service/Named Pipes og AppContainer isolation.'
status: draft
tags:
- task
- windows
- service
- appcontainer
- sandbox
- supervisor
- future
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-30T09:07:00Z'
---

# Task 037: Windows Service and AppContainer Sandbox Platform Seam

**Status**: `DRAFT` (Planlagt til fremtidig release)  
**Intent**: `🚀 NEW FEATURE`  
**Oprettet**: `2026-08-30`  

## 🎯 Formål
Tilføje fuld native platformunderstøttelse for **Windows (Windows 10/11 og Windows Server)** til `agent-gauntlet`'s lokale supervisorarkitektur:
1. Implementere `WindowsServiceManager` under `ServiceManagerSeam` ved hjælp af Windows Service Control Manager (SCM) og Named Pipes / AF_UNIX sockets (`\\.\pipe\agent-gauntlet-supervisor`).
2. Implementere `AppContainerSandboxRunner` under `SandboxRunnerSeam` ved hjælp af Windows AppContainer process isolation og low-privilege tokens med deaktiveret netværksadgang.
3. Håndtere Windows-specifikke path-separatorer (`\`), NTFS ACL-rettigheder og CRLF-normalisering i det kanoniske manifest.
4. Opsætte dedikeret Windows GitHub Actions CI-matrix runner til empirisk E2E-verifikation.

## 📋 Acceptance Criteria
- [ ] Implementere `WindowsServiceManager` i bootstrapperen med sikker registrering og fjernelse af Windows Service.
- [ ] Etablere IPC-kommunikation via Windows Named Pipes eller AF_UNIX med eksplicitte DACLs (kun aktuel bruger/system).
- [ ] Implementere `AppContainerSandboxRunner`, der isolerer testafvikling fra værtens filsystem uden adgang til netværk.
- [ ] Verificere at kanonisk workspace manifest fungerer identisk på Windows uanset CRLF eller path-formatering.
- [ ] Tilføje Windows GitHub Actions test-job i `.github/workflows/ci.yml` (`windows-latest`).
- [ ] Køre fuld E2E-test på Windows og bevise, at `LOCAL_SUPERVISED` rapport genereres og verificeres fejlfrit.

## 🚫 Must NOT
- Må IKKE påstå eller markere Windows som officielt understøttet, før alle end-to-end tests kører grønt på en ægte Windows runner.
- Må IKKE anvende `sudo` eller usikre globale permissions på Named Pipes.

## 📝 Revisions
- 2026-08-30: Oprettet som dedikeret opgavepakke for Windows-udvidelse efter v0.4.0 Linux-stabilisering.

## 🧪 Verifikation
- `npm run test:e2e:windows` på Windows GitHub runner.
- Verifikation af Named Pipe DACLs og AppContainer isolation.
