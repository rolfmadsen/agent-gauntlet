# Agent-Gauntlet Roadmap & Fremtidige Udvidelser

Dette dokument samler og prioriterer udvidelser og modenheds-features for `agent-gauntlet`, destilleret fra referencedokumenterne i [`old-coder/skills/old-coder/references/`](../old-coder/skills/old-coder/references/).

---

## 🏛️ Arkitektur-Model: Vertical Slice Architecture (Package-by-Feature)

`agent-gauntlet` er arkitektonisk opbygget efter **Vertical Slice Architecture / Package-by-Feature (Screaming Architecture)** jf. [ADR 0001](docs/adr/0001-package-by-feature-architecture.md), hvor hver feature og hver harness-integration udgør en selvstændig, afgrænset vertikal slice:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   HARNESS-AGNOSTISK KERNE (CORE)                       │
│  (100% uafhængig verifikationsmotor, CLI og kryptografisk evidens)     │
│                                                                        │
│  ├── features/gauntlet/     (Procesafvikling, fail-closed, timeouts)   │
│  ├── features/evidence/     (Source manifest, Verification reports, Sigstore DSSE attestation) │
│  ├── features/diagnostics/  (Strukturerede LLM-remediations & AST)     │
│  ├── features/stacks/       (Python, TypeScript, Rust autodetektion)   │
│  └── features/config/       (gauntlet.toml / gauntlet.json)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   ADAPTER- OG PLUGIN-LAG (HARNESSES)                   │
│  (Hver platform har sin egen plugin-, hook- og instruktions-bridge)    │
│                                                                        │
│  ├── 🟢 Google Antigravity: .agents/plugins/, hooks.json, HUD, skills  │
│  ├── 🔵 Claude Code:       CLAUDE.md -> .agents/AGENTS.md, .claude/    │
│  ├── 🟡 Cursor (IDE):       .cursor/rules/gauntlet.mdc -> .agents/     │
│  ├── 🌊 Windsurf (Cascade): .windsurfrules / .windsurf/rules/          │
│  ├── 🐙 GitHub Copilot:    .github/copilot-instructions.md -> .agents/ │
│  └── 🟣 DeepSeek/OpenHands: CONVENTIONS.md / AGENTS.md, CoT-diagnostics│
└────────────────────────────────────────────────────────────────────────┘
```

Da hver platform (Google Antigravity IDE, Claude Code, Cursor, Windsurf, GitHub Copilot m.fl.) har sin egen plugin-, hook- og prompt-model, implementeres understøttelsen via isolerede adaptere, der varetager:
1. **Autoritativ Instruktions-Bridge**: En letvægts entrypoint-fil i platformens forventede format/sti, der refererer autoritativt til projektets centrale regler i `.agents/AGENTS.md` og `.agents/rules/`.
2. **Tool- & Hook-Mapping**: Oversættelse mellem platformens værktøjer/hændelser og gatekeeperens `evaluate_tool_invocation`.
3. **Plugin Packaging & Manifests**: Format-specifikke konfigurationer (`plugin.json`, `.claude/settings.json`, `.cursor/rules/*.mdc`).
4. **Scaffolding & Installation**: `agent-gauntlet init --harness <navn>` tilpasset målmiljøet.

---

## 🗺️ Prioriteret Feature Oversigt

| Rangering | Feature / Opgave | Formål | Kilde / Reference | Prioritet / Status |
|:---:|---|---|---|:---:|
| **1** | **Google Antigravity IDE Plugin & Adapter** | Fuld implementering af Antigravity plugin-arkitektur (`.agents/plugins/agent-gauntlet/`), `hooks.json`, Response HUD og skills | [Beskrivelse](#1--google-antigravity-ide-plugin--adapter-fuldført--reference) | **FULDFØRT (REFERENCE)** |
| **2** | **Claude Code Adapter & `CLAUDE.md` Bridge** | Fuld understøttelse af Claude Code i gatekeeper, tool-aliasing (`Bash`, `Edit`, `Write`), `CLAUDE.md` bridge og `.claude/` hooks | [Beskrivelse](#2--claude-code-adapter--claudemd-bridge) | **FULDFØRT (Task 007)** |
| **3** | **Cursor Adapter & `.cursor/rules/` Bridge** | Scaffolding af `.cursor/rules/agent-gauntlet.mdc` (og `.cursorrules`) der peger autoritativt på `.agents/AGENTS.md` | [Beskrivelse](#3--cursor-ide-adapter--cursorrulesmdc-bridge) | **KLARGJORT (Task 030)** |
| **4** | **Windsurf Adapter & `.windsurfrules` Bridge** | Scaffolding af `.windsurfrules` og `.windsurf/rules/` cascade-regler med bridge til `.agents/AGENTS.md` | [Beskrivelse](#4--windsurf-cascade-adapter--windsurfrules-bridge) | **KLARGJORT (Task 031)** |
| **5** | **GitHub Copilot & OpenAI/Codex Bridge** | Scaffolding af `.github/copilot-instructions.md` med autoritativ reference til `.agents/AGENTS.md` | [Beskrivelse](#5--github-copilot--openaicodex-bridge) | **KLARGJORT (Task 032)** |
| **6** | **DeepSeek & OpenHands/Aider Adapter** | `CONVENTIONS.md` bridge, CoT Actionable Diagnostics og token-komprimeret spec-ingestion for open-weights modeller | [Beskrivelse](#6--deepseek-harness--reasoner-integration-openhands--aider) | **FREMTIDIG UDVIDELSE** |
| **7** | **Changed-Line Differential Coverage** | Gennemtvinger 100% test- og forgreningstjek på *udelukkende* ændrede/tilføjede linjer i git diff | [`gauntlet.md`](../old-coder/skills/old-coder/references/gauntlet.md) | **KLARGJORT (Task 033)** |
| **8** | **Spec $\to$ Test Mapping & "Must NOT" Validator** | Mekanisk 1:1 håndhævelse af at alle Gherkin-scenarier og negative begrænsninger ("Must NOT") har specifikke tests | [`templates.md`](../old-coder/skills/old-coder/references/templates.md) | **HØJ** |
| **9** | **Fresh-Context Adversarial Verifier** | Uafhængig sub-agent i ren session, der blindt angriber koden for blinde vinkler, test-gaming og spec-drift | [`verifier.md`](../old-coder/skills/old-coder/references/verifier.md), [`verifier-case-study.md`](../old-coder/skills/old-coder/references/verifier-case-study.md) | **MEDIUM** |
| **10** | **Extended Security & Supply-Chain Audits** | Automatiserede gauntlet-lag for `secret-scan` (`gitleaks`) og pakkesårbarheder (`pip-audit`, `npm audit`, `cargo-audit`) | [`gauntlet.md`](../old-coder/skills/old-coder/references/gauntlet.md) | **MEDIUM** |
| **11** | **Suite Health & Test-Order Randomizer** | Randomiseret testrækkefølge med deterministisk seed for at afsløre globale tilstandslækager og flakiness | [`gauntlet.md`](../old-coder/skills/old-coder/references/gauntlet.md) | **LAV** |

---

## 💡 Begrundelse for Prioritering & Udviklingsrækkefølge

1. **Rangering 1 & 2: Google Antigravity & Claude Code (Fundamentet på Plads)**
   - Google Antigravity IDE og Claude Code udgør vores fuldt implementerede reference-adaptere med `CLAUDE.md` og `.agents/hooks.json` integration jf. Task 007.
2. **Rangering 3, 4, 5 & 6: Cursor, Windsurf, Copilot & OpenHands Bridges (Multi-Harness Scaffolding)**
   - Etablerer letvægts instruction-bridges (`.cursor/rules/`, `.windsurfrules`, `.github/copilot-instructions.md`, `CONVENTIONS.md`), så ethvert udviklermiljø automatisk understøttes via `agent-gauntlet init --harness <navn>`.
3. **Rangering 7: Changed-Line Differential Coverage (Højeste Pragmatiske Værdi)**
   - Deterministisk, matematisk kontrol der sikrer 100% test- og branch-dækning på al ny kode og bugfixes uden at kræve 100% dækning af legacy-kodebasen.
4. **Rangering 8: Spec $\to$ Test Mapping & "Must NOT" Validator (TDD-Garant)**
   - Sikrer at AI-agenten ikke tager lette genveje eller ignorerer negative begrænsninger ("Must NOT") og vanskelige kanttilfælde.
5. **Rangering 9: Fresh-Context Adversarial Verifier (Avanceret Second Opinion)**
   - Enorm værdi mod test-gaming, bygget oven på en isoleret kontekst via harness eller sub-agent.
6. **Rangering 10: Extended Security & Supply-Chain Audits (Lavthængende Frugter)**
   - Vigtigt mod læk af hemmeligheder og sårbare pakker, tilføjes deklarativt i `gauntlet.toml`.
7. **Rangering 11: Suite Health & Test-Order Randomizer (Optimering)**
   - Fjerner subtile tilstandslækager i testsuiter.

---

## 🔍 Detaljerede Feature Beskrivelser

### 1. 🛡️ Google Antigravity IDE Plugin & Adapter (Fuldført & Reference)
* **Koncept**:
  Fuldendt, robust integration med Google Antigravity IDE's officielle plugin- og hook-system:
  1. **Plugin Manifest & Packaging**: Komplet `plugins/agent-gauntlet/plugin.json` og distribution af bundled skills (`old-coder`, `grill-me`, `grill-with-docs`, `diagnose`).
  2. **Pre-Invocation Hook Gatekeeper**: Sikker validering af `run_command`, `write_to_file`, `replace_file_content` og `multi_replace_file_content` via `.agents/hooks.json`.
  3. **Task HUD & State Generator**: Automatisk generering af Task HUD og session handoff prompts tilpasset Antigravity chat-miljøet.

---

### 2. 🔌 Claude Code Adapter & `CLAUDE.md` Bridge
* **Koncept**:
  Fuld integration med Anthropic's **Claude Code** CLI og agent-økosystem jf. Task 007:
  1. **Autoritativ Regelbro (`CLAUDE.md`)**: Automatisk oprettelse af en rod-`CLAUDE.md`, der autoritativt henviser agenten til `.agents/AGENTS.md` og `.agents/rules/`.
  2. **Tool-Call Normalisering**: Gatekeeper-mapping for Claude Code's værktøjer (`Bash` $\to$ `run_command`, `Edit`/`Write` $\to$ `replace_file_content`/`write_to_file`, `View` $\to$ `view_file`).
  3. **Claude Hooks Scaffolding**: Automatisk opsætning af `.claude/settings.json` eller Claude Code pre-execution hooks, der eksekverer `gatekeeper.py`.

---

### 3. 🎯 Cursor IDE Adapter & `.cursor/rules/*.mdc` Bridge
* **Koncept**:
  Dedikeret adapter og scaffolding for **Cursor IDE**:
  1. **Autoritativ Regelbro (`.cursor/rules/agent-gauntlet.mdc`)**: Opretter en modulær regel i `.cursor/rules/` med YAML-frontmatter (`alwaysApply: true`), der instruerer Cursor-agenten i at læse og overholde `.agents/AGENTS.md` og `.agents/rules/`.
  2. **Legacy Fallback (`.cursorrules`)**: Valgfri generering af en rod-`.cursorrules` fil for ældre Cursor-versioner.
  3. **Scaffolding Integration**: `agent-gauntlet init --harness cursor` klargør automatisk `.cursor/rules/` strukturen.

---

### 4. 🌊 Windsurf (Cascade) Adapter & `.windsurfrules` Bridge
* **Koncept**:
  Integration til Codeium's **Windsurf IDE** og Cascade agent-motor:
  1. **Autoritativ Regelbro (`.windsurfrules` & `.windsurf/rules/`)**: Opretter en slank `.windsurfrules` entrypoint-fil i projektets rod, der instruerer Cascade i at læse `.agents/AGENTS.md` og håndhæve Task HUD & TDD-cyklus.
  2. **Cascade Workflows**: Mulighed for at synkronisere `.agents/workflows/` til Windsurf Cascade workflows.
  3. **Scaffolding Integration**: `agent-gauntlet init --harness windsurf`.

---

### 5. 🐙 GitHub Copilot & OpenAI/Codex Bridge
* **Koncept**:
  Understøttelse af **GitHub Copilot Workspace / Chat** samt OpenAI Codex/Assistant interfaces:
  1. **Autoritativ Regelbro (`.github/copilot-instructions.md`)**: Etablerer standarden for GitHub Copilot i `.github/`, som instruerer Copilot i projektets TDD-disciplin, Task-krav og forbyder kildekode-ændringer uden en aktiv task i `tasks/`.
  2. **Scaffolding Integration**: `agent-gauntlet init --harness copilot` eller `agent-gauntlet init --harness codex`.

---

### 6. 🧠 DeepSeek-Harness & Reasoner Integration (OpenHands / Aider)
* **Koncept**:
  Specialiseret integration til **DeepSeek** (R1/V3) og lignende avancerede ræsonneringsmodeller afviklet via OpenHands, Aider eller headless API-harnesses:
  1. **Autoritativ Regelbro (`CONVENTIONS.md` & `AGENTS.md`)**: Automatisk mapping for headless CLI-værktøjer som Aider og OpenHands.
  2. **Chain-of-Thought Remediation Engine**: Formatering af `DiagnosticReport` og `DiagnosticFinding` til ultra-kompakte, strukturerede prompts optimeret til modeller med dybe `<think>` ræsonneringsspor.
  3. **Headless Execution Bridge**: CLI- og JSON-interfacer skræddersyet til automatiserede agent-loops (f.eks. OpenHands benchmark runs).

---

### 4. 🎯 Changed-Line Differential Coverage (`diff-cover`)
* **Koncept**:
  Et præcisions-verifikationslag, der isolerer den aktuelle Git-diff og beregner testdækning for kun de linjer, der er rørt ved i opgaven.
* **Hvorfor det er vigtigt**:
  * Tvinger 100% test- og branch-dækning på al ny kode og bugfixes.
  * Realistisk i eksisterende, store kodebaser: Projektet behøver ikke have 100% total dækning for at nye ændringer er højt verificerede.

---

### 5. 📋 Mekanisk Spec $\to$ Test Mapping & "Must NOT" Invariant Validator
* **Koncept**:
  En parser der forbinder hvert enkelt scenarie i opgaven samt hver negative begrænsning ("Must NOT") direkte med specifikke testmetoder (`test_file.py::test_scenario_name`).
* **Hvorfor det er vigtigt**:
  * Forhindrer agenten i at springe ubehagelige fejltilfælde eller negative sikkerhedskrav over.
  * Gør `evidence.md` tabellen fuldstændig mekanisk verificerbar uden menneskelig gætteleg.

---

### 6. 🕵️ Fresh-Context Adversarial Verifier Protocol (`agent-gauntlet verifier`)
* **Koncept**: 
  En dedikeret CLI-kommando og orkestreringsloop, der spawner en uafhængig sub-agent i en *helt isoleret kontekst* med præcis 4 blinde inputs:
  1. Den godkendte opgavekontrakt/SPEC.
  2. Kildekodens aktuelle `tree-hash`.
  3. Gauntlet entry point (`gauntlet.toml` / `tools/gauntlet.sh`).
  4. Et rent snapshot af kildekoden.
* **Hvad den fanger**:
  * Test-gaming (kode skrevet specifikt til at snyde testens mock-objekter).
  * Blinde vinkler og manglende grænseværditjek (f.eks. `NaN`, memory exhaustion, race conditions).
  * Spec-drift hvor koden og specifikationen taler forbi hinanden.
* **Styring & Loft**:
  * To-faset angreb: Blind pass $\to$ Sammenligning med draft `evidence.json`.
  * Hård begrænsning på maks 2 runder med differentieret grading (`behavioural` vs `description/mapping`).

---

### 7. 🔒 Extended Security & Supply-Chain Audit Layers
* **Koncept**:
  Indbygge valgfrie plug-and-play gauntlet-lag til:
  * `secret-scan`: Forhindrer at nøgler, tokens eller passwords begås i koden (via `gitleaks`).
  * `pkg-audit`: Validerer at nyindførte afhængigheder ikke indeholder kendte CVE'er (via `pip-audit`, `npm audit`, `cargo-audit`).
  * `capability-diff`: Sikrer at agenten ikke utilsigtet introducerer nye netværks- eller procesrettigheder i koden.

---

### 8. 🎲 Suite Health & Test-Order Randomizer
* **Koncept**:
  Køre testsuiterne i randomiseret rækkefølge med fast seed (`pytest-randomly`, `vitest --sequence.shuffle`, `go test -shuffle=on`).
* **Hvorfor det er vigtigt**:
  * Opdager hvis tests i virkeligheden deler tilstand (f.eks. efterladte database-rækker, singleton-mutationer, globale mocks) og kun består, fordi de køres i en bestemt rækkefølge.

---

## 📅 Næste Skridt
Google Antigravity IDE er det primære fuldt implementerede og verificerede harness. Når roadmap-arbejdet fortsættes, kan specifikke adaptere udrulles trinvist.



