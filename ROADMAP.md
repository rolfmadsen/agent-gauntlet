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
│  (Hver platform har sin egen plugin- og hook-arkitektur)               │
│                                                                        │
│  ├── 🟢 Google Antigravity: .agents/plugins/, hooks.json, HUD, skills  │
│  ├── 🔵 Claude Code:       CLAUDE.md, .claude/ hooks, tool-aliasing    │
│  ├── 🟣 DeepSeek/OpenHands: CoT-diagnostics, prompt-pakker, headless   │
│  └── 🟡 Generic MCP:        Model Context Protocol server (Cursor mfl) │
└────────────────────────────────────────────────────────────────────────┘
```

Da hver platform (Google Antigravity IDE, Claude Code, DeepSeek m.fl.) har sin egen plugin- og hook-model, implementeres understøttelsen via isolerede adaptere, der varetager:
1. **Tool- & Hook-Mapping**: Oversættelse mellem platformens værktøjer/hændelser og gatekeeperens `evaluate_tool_invocation`.
2. **Plugin Packaging & Manifests**: Format-specifikke konfigurationer (`plugin.json`, `.claude/settings.json`, system-prompts).
3. **Scaffolding & Installation**: `agent-gauntlet init --harness <navn>` tilpasset målmiljøet.

---

## 🗺️ Prioriteret Feature Oversigt

| Rangering | Feature / Opgave | Formål | Kilde / Reference | Prioritet / Status |
|:---:|---|---|---|:---:|
| **1** | **Google Antigravity IDE Plugin & Adapter** | Fuld implementering af Antigravity plugin-arkitektur (`.agents/plugins/agent-gauntlet/`), `hooks.json`, Response HUD og skills | [Beskrivelse](#1--google-antigravity-ide-plugin--adapter-nuværende-fokus) | **FØRSTEPRIORITET (NUVÆRENDE)** |
| **2** | **Claude Code Plugin & Adapter Integration** | Fuld understøttelse af Claude Code i gatekeeper, tool-aliasing (`Bash`, `Edit`, `Write`), `.claude/` hooks og scaffolding | [Beskrivelse](#2--claude-code-plugin--adapter-integration) | **FREMTIDIG UDVIDELSE** |
| **3** | **DeepSeek-Harness & Reasoner Integration** | Kompakt Actionable Diagnostics pipeline optimeret til DeepSeek/OpenHands/Aider og Chain-of-Thought ræsonnering | [Beskrivelse](#3--deepseek-harness--reasoner-integration) | **FREMTIDIG UDVIDELSE** |
| **4** | **Changed-Line Differential Coverage** | Gennemtvinger 100% test- og forgreningstjek på *udelukkende* ændrede/tilføjede linjer i git diff | [`gauntlet.md`](../old-coder/skills/old-coder/references/gauntlet.md) | **HØJ** |
| **5** | **Spec $\to$ Test Mapping & "Must NOT" Validator** | Mekanisk 1:1 håndhævelse af at alle Gherkin-scenarier og negative begrænsninger ("Must NOT") har specifikke tests | [`templates.md`](../old-coder/skills/old-coder/references/templates.md) | **HØJ** |
| **6** | **Fresh-Context Adversarial Verifier** | Uafhængig sub-agent i ren session, der blindt angriber koden for blinde vinkler, test-gaming og spec-drift | [`verifier.md`](../old-coder/skills/old-coder/references/verifier.md), [`verifier-case-study.md`](../old-coder/skills/old-coder/references/verifier-case-study.md) | **MEDIUM** |
| **7** | **Extended Security & Supply-Chain Audits** | Automatiserede gauntlet-lag for `secret-scan` (`gitleaks`) og pakkesårbarheder (`pip-audit`, `npm audit`, `cargo-audit`) | [`gauntlet.md`](../old-coder/skills/old-coder/references/gauntlet.md) | **MEDIUM** |
| **8** | **Suite Health & Test-Order Randomizer** | Randomiseret testrækkefølge med deterministisk seed for at afsløre globale tilstandslækager og flakiness | [`gauntlet.md`](../old-coder/skills/old-coder/references/gauntlet.md) | **LAV** |

---

## 💡 Begrundelse for Prioritering & Udviklingsrækkefølge

1. **Rangering 1: Google Antigravity IDE Plugin & Adapter (Nuværende Fokus & Testmiljø)**
   - *Hvorfor først*: Google Antigravity IDE er det aktive testmiljø. Ved at færdiggøre og raffinere plugin-pakken, Response HUD og gatekeeper-hooket her, opnås et gennemprøvet reference-mønster for, hvordan harness-adaptere skal opbygges.
2. **Rangering 2: Claude Code Plugin & Adapter Integration (Multi-Harness Fundament)**
   - *Hvorfor*: Gør `agent-gauntlet`'s gatekeeper, task-binding og evidensverifikation kompatibel med Anthropic Claude Code terminal-arbejdsgange via tool-aliasing (`Bash`, `Edit`, `Write`) og dedikerede Claude-hooks.
3. **Rangering 3: DeepSeek-Harness & Reasoner Integration (Open-Source / API-Harnesses)**
   - *Hvorfor*: Sikrer at ræsonneringsmodeller (f.eks. DeepSeek R1/V3) i harnesses som OpenHands eller Aider modtager ultra-kompakte, strukturerede diagnostik-feeds tilpasset store Chain-of-Thought ræsonneringsforløb.
4. **Rangering 4: Changed-Line Differential Coverage (Højeste Pragmatiske Værdi)**
   - *Hvorfor*: Deterministisk, matematisk kontrol der sikrer 100% test- og branch-dækning på al ny kode og bugfixes uden at kræve 100% dækning af legacy-kodebasen.
5. **Rangering 5: Spec $\to$ Test Mapping & "Must NOT" Validator (TDD-Garant)**
   - *Hvorfor*: Sikrer at AI-agenten ikke tager lette genveje eller ignorerer negative begrænsninger ("Must NOT") og vanskelige kanttilfælde.
6. **Rangering 6: Fresh-Context Adversarial Verifier (Avanceret Second Opinion)**
   - *Hvorfor*: Enorm værdi mod test-gaming, men bygger naturligt oven på en velfungerende Multi-Harness arkitektur, da den skal kunne spawne sub-agenter via API/harness.
7. **Rangering 7: Extended Security & Supply-Chain Audits (Lavthængende Frugter)**
   - *Hvorfor*: Vigtigt mod læk af hemmeligheder og sårbare pakker, men tilføjes let som simple deklarative lag i `gauntlet.toml`.
8. **Rangering 8: Suite Health & Test-Order Randomizer (Optimering)**
   - *Hvorfor*: Fjerner subtile tilstandslækager i testsuiter, men er en optimering oven på en allerede moden testbase.

---

## 🔍 Detaljerede Feature Beskrivelser

### 1. 🛡️ Google Antigravity IDE Plugin & Adapter (Nuværende Fokus)
* **Koncept**:
  Fuldendt, robust integration med Google Antigravity IDE's officielle plugin- og hook-system:
  1. **Plugin Manifest & Packaging**: Komplet `plugins/agent-gauntlet/plugin.json` og distribution af bundled skills (`old-coder`, `grill-me`, `grill-with-docs`, `diagnose`).
  2. **Pre-Invocation Hook Gatekeeper**: Sikker validering af `run_command`, `write_to_file`, `replace_file_content` og `multi_replace_file_content` via `.agents/hooks.json`.
  3. **Task HUD & State Generator**: Automatisk generering af Task HUD og session handoff prompts tilpasset Antigravity chat-miljøet.
* **Hvorfor det er vigtigt**:
  * Fungerer som testet reference-adapter for alle fremtidige harness-tilkoblinger.

---

### 2. 🔌 Claude Code Plugin & Adapter Integration
* **Koncept**:
  Etablere fuld tovejs-integration med Anthropic's **Claude Code** CLI og agent-økosystem:
  1. **Tool-Call Normalisering**: Gatekeeper-mapping for Claude Code's værktøjer (`Bash` $\to$ `run_command`, `Edit`/`Write` $\to$ `replace_file_content`/`write_to_file`, `View` $\to$ `view_file`).
  2. **Claude Hooks Scaffolding**: Automatisk opsætning af `.claude/settings.json` eller Claude Code pre-execution hooks, der eksekverer `gatekeeper.py`.
  3. **Autoritativ Regelbro**: Automatisk synkronisering og bridging mellem `CLAUDE.md` og `.agents/AGENTS.md`.
* **Hvorfor det er vigtigt**:
  * Udvider `agent-gauntlet`'s strenge TDD- og gatekeeper-disciplin til Claude Code-brugere uden manuelle tilpasninger.

---

### 3. 🧠 DeepSeek-Harness & Reasoner Integration
* **Koncept**:
  Specialiseret integration til **DeepSeek** (R1/V3) og lignende avancerede ræsonneringsmodeller afviklet via OpenHands, Aider eller headless API-harnesses:
  1. **Chain-of-Thought Remediation Engine**: Formatering af `DiagnosticReport` og `DiagnosticFinding` til ultra-kompakte, strukturerede prompts optimeret til modeller med dybe `<think>` ræsonneringsspor.
  2. **Token-komprimeret Spec & Task Ingestion**: Eliminering af overflødig støj i fejllogs for at spare ræsonnerings-tokens i store multi-turn sessions.
  3. **Headless Execution Bridge**: CLI- og JSON-interfacer skræddersyet til automatiserede agent-loops (f.eks. OpenHands benchmark runs).
* **Hvorfor det er vigtigt**:
  * Åbner for kørsel af `agent-gauntlet` med open-weights og cost-effektive ræsonneringsmodeller med maksimal præcision.

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



