<p align="center">
  <a href="#-hurtig-start--installation"><b>🚀 Hurtig Start & Installation</b></a> •
  <a href="#-pipeline-og-gates-sådan-virker-det"><b>🧭 Pipeline & Gates</b></a> •
  <a href="#-arkitektur--designprincipper"><b>🎯 Arkitektur</b></a> •
  <a href="#️-mappestruktur-package-by-feature"><b>🏗️ Mappestruktur</b></a> •
  <a href="#️-fuld-cli-reference"><b>🛠️ CLI Reference</b></a> •
  <a href="#-python-api"><b>💻 Python API</b></a> •
  <a href="#️-arkitektur-adrs"><b>🏛️ ADRs</b></a> •
  <a href="CHANGELOG.md"><b>Changelog</b></a>
</p>

---

<p align="center">
  <img src="docs/assets/spiessgasse-gauntlet.png" alt="agent-gauntlet — Running the Gauntlet" width="640" /><br/>
  <em>»Spiessgasse« (Pike-Alley / <a href="https://en.wikipedia.org/wiki/Running_the_gauntlet">Running the Gauntlet</a>) — <a href="https://en.wikipedia.org/wiki/Jost_Amman">Jost Amman</a> illustration, Kriegs Ordnung (1564)</em>
</p>

<h1 align="center">agent-gauntlet 🛡️</h1>

<p align="center">
  <em>Universel multi-stack verifikations- og actionable diagnostics motor bygget på Robert C. Martin ("Uncle Bob") TDD & Clean Craftsmanship</em>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/@agent-gauntlet/cli"><img src="https://img.shields.io/npm/v/@agent-gauntlet/cli.svg?color=blue" alt="NPM Version" /></a>
  <a href="https://github.com/rolfmadsen/agent-gauntlet/actions/workflows/ci.yml"><img src="https://github.com/rolfmadsen/agent-gauntlet/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI" /></a>
  <a href="tools/mutants.py"><img src="https://img.shields.io/badge/mutants%20killed-100%25-brightgreen.svg" alt="Mutants Killed" /></a>
  <a href="docs/adr/0007-local-transparent-supervisor-and-wasm-verifier.md"><img src="https://img.shields.io/badge/evidence-Three--Tier%20Trust%20Model-blue.svg" alt="Evidence Model" /></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg" alt="Python Version" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT" /></a>
</p>

---

**Dokumentation**: [Makro-Spec](spec.md) • [Domæne-Glossary](CONTEXT.md) • [Kodestandarder](CODING_STANDARDS.md) • [Arkitektur (ADRs)](docs/adr/) • [Changelog](CHANGELOG.md)

**Kildekode & Pakker**: [GitHub](https://github.com/rolfmadsen/agent-gauntlet) • [NPM Pakke](packages/agent-gauntlet)

---

**agent-gauntlet** omgiver AI-genereret kode med et kompromisløst verifikations-gauntlet (Linters, Type-checkere, Unit tests, Property- og Invariant-tests, Mutationsafprøvning, privilege-separated Local Supervisor med WASM policy engine og Three-Tier evidens & attestering jf. [ADR 0005](docs/adr/0005-two-tier-verification-and-attestation-model.md) & [ADR 0007](docs/adr/0007-local-transparent-supervisor-and-wasm-verifier.md)) og oversætter rå fejludskrifter til **Actionable Diagnostics** i et feedback-loop, som AI-agenter kan handle direkte på.

---

## 🚀 Hurtig Start & Installation

Kom i gang på under 1 minut uden forudgående installation via NPX:

### 1. Initialiser dit projekt
Stil dig i rodmappen på dit projekt (TypeScript, Python, Rust eller polyglot) og kør:

```bash
# Åbn dit projektkatalog
cd ~/sti/til/dit-projekt

# Scaffold samtlige in-repo styringsfiler direkte via NPX
npx @agent-gauntlet/cli init
```

#### 📦 Hvad `agent-gauntlet init` opretter lokalt i projektet (In-Repo Single Source of Truth):
| Fil / Mappe | Formål |
|---|---|
| [`gauntlet.toml`](gauntlet.toml) | Deklarativ konfiguration af linter, types, tests, mutation testing |
| [`CONTEXT.md`](CONTEXT.md) | Domæne-glossary for projektet (Aristoteles' *definitio per genus et differentiam*) |
| [`CODING_STANDARDS.md`](CODING_STANDARDS.md) | Multi-stack kodestandarder (Python, TypeScript & React, Rust og Cross-Stack Boundary Invariants) |
| [`spec.md`](spec.md) | Makro-specifikation og system-invarianter |
| [`tasks/001-bootstrap.md`](tasks/) | Opgavemappe til håndhævelse af task-kontrakter & acceptkriterier |
| [`docs/adr/`](docs/adr/) | Architecture Decision Records (ADR) til projekt-specifikke beslutninger |
| [`.agents/AGENTS.md`](.agents/AGENTS.md) | AI-agent retningslinjer, Response HUD og task-management protokoller |
| [`.agents/hooks.json`](.agents/hooks.json) | Pre-Invocation Hook til Stop/Go gatekeeperen |
| [`.agents/skills/`](.agents/skills/) | Bundled skills (`old-coder`, `grill-me`, `grill-with-docs`, `diagnose`, `code-review`) |

> [!TIP]
> **🛡️ Ikke-destruktiv & Kontekstbevidst Garanti (Safety First):**  
> `agent-gauntlet init` overskriver **aldrig** eksisterende filer i dit projekt, medmindre du udtrykkeligt angiver `--force`. Modne projekter forurenes ikke med starter-skabeloner, når eksisterende opgaver eller ADR'er allerede er til stede.

### 2. Kør Verifikation & Tjek Evidens
Når du eller agenten arbejder på en opgave i projektet, afvikles gauntlettet direkte:

```bash
# Kør gauntlet og forseg evidens for en opgave:
npx @agent-gauntlet/cli verify --task-id 001-bootstrap

# Start den lokale supervisor som baggrundstjeneste:
npx @agent-gauntlet/cli supervisor start --daemon

# Tjek supervisor socket og dæmonstatus:
npx @agent-gauntlet/cli supervisor status

# Kør host- og isolation-diagnostik (Node, Rust/Cargo, bwrap, tsconfig):
npx @agent-gauntlet/cli doctor

# Valider dokumentation & OKF v0.2 metadata:
npx @agent-gauntlet/cli okf validate
```

> [!IMPORTANT]
> **🚪 Zero Lock-in & Ren Afinstallation (Clean Uninstall):**  
> Da alt ligger lokalt i projektets Git-træ, slettes `agent-gauntlet` fra et projekt med én simpel kommando uden at efterlade globale ændringer på maskinen:
> ```bash
> rm -rf .agents tasks docs/adr CONTEXT.md CODING_STANDARDS.md spec.md gauntlet.toml evidence.json evidence.md verification-report.json
> ```

---

## 🧭 Pipeline og Gates: Sådan virker det

I `agent-gauntlet` understøttes udvikleren af en deterministisk pipeline, der holder AI-agenten i kort snor. Systemet arbejder på to adskilte niveauer:

1. **Metodiske retningslinjer (Agent Skills)**: Proceskrav (såsom grilling, TDD-disciplin og arkitektur-review), som agenten instrueres i at følge via sine prompt- og workflow-skabeloner (`grill-me`, `old-coder`, `code-review`).
2. **Håndhævede software-gates (CLI & Runtime Guards)**: Deterministiske kontrolpunkter i Python-koden (`check-spec`, pre-invocation hooks / Bubblewrap-sandbox, `verify`, `check-evidence` og `check-release`), der fysisk blokerer uautoriserede handlinger med exit-koder og multi-digest integritetskontrol.

> [!NOTE]
> **Bemærk om tilstande:** Systemet styres ikke af en global database over opgavestatus, men af diskrete, uafhængige CLI-kald. Komponenten `SessionFsm` i supervisor-kernen styrer udelukkende opgavesessionens tilstandsmaskine (`DISCOVERED`, `ACTIVE`, `VERIFYING`, `PASSED`, `FAILED`, `INVALIDATED`, `CLOSED`).

### Oversigt over udviklingsflowet

```text
[ 1. IDÉAFKLARING ]             ──► Metodisk skill (grill-me / grill-with-docs)
         │                          (Opdaterer CONTEXT.md & docs/adr/)
         ▼
[ 2. SPECIFIKATION ]            ──► HÅRD GATE: agent-gauntlet check-spec
         │                          (OKF metadata, formål, kriterier, Must NOT, Aristoteles-glossar)
         ▼
[ 3. TDD & KODNING ]            ──► HÅRD GATE: Gatekeeper Hooks & Bubblewrap Sandbox
         │                          (Kræver aktiv task for beskyttede stier, forhindrer git push)
         ▼
[ 4. FLERLAGS VERIFIKATION ]    ──► HÅRD GATE: agent-gauntlet verify
         │                          (Kører linters, typer, tests, mutationer; genererer digests)
         ▼
[ 5. KODESTANDARD-REVIEW ]      ──► Hybrid skill: code-review & udvikleraccept
         │                          (Audit mod CODING_STANDARDS.md)
         ▼
[ 6. DRIFT-KONTROL ]            ──► HÅRD GATE: agent-gauntlet check-evidence
         │                          (Verificerer at workspace matcher rapporten; i CI: check-attestation)
         ▼
[ 7. RELEASE READINESS ]        ──► HÅRD GATE: agent-gauntlet check-release
                                    (Versionssynkronisering, CHANGELOG.md og ADR-krydsreferencer)
```

### Pipelinen trin for trin

#### 1. Idé- og kontekstafklaring
* **Type**: Metodisk proces (Agent Skill)
* **Hvad der sker**: Før der skrives specifikationer eller kode, aktiveres grilling-skills (`grill-me` eller `grill-with-docs`). Agenten udfordrer antagelser, identificerer risici og afstemmer planer mod eksisterende arkitektur og ADR'er.
* **Kontrolpunkt**:
  * *Hvem godkender*: Udvikleren i direkte dialog.
  * *Hvordan*: Dialogen udmønter sig i, at agenten opdaterer `CONTEXT.md` og eventuelt udarbejder en ny ADR i `docs/adr/`.
  * *Håndhævelse i koden*: Dette er et instruktionskrav til agenten. Der findes ingen automatisk kodelås, der forhindrer oprettelse af tasks uden forudgående grilling; disciplinen bæres af udviklerens sparring med agenten.

#### 2. Specifikation & Opgavebinding
* **Type**: Hård software-gate
* **Hvad der sker**: Opgaven defineres formelt i en markdown-fil under `tasks/` (f.eks. `tasks/045-min-feature.md`) med eksplicit OKF-frontmatter samt eksekverbare acceptkriterier.
* **Kontrolpunkt**: Spec Gate (`agent-gauntlet check-spec`)
  * *Hvem godkender*: `spec_gate.py` (assisteret af `tasks/parser.py`).
  * *Hvordan*: CLI-værktøjet parser task-filen og validerer:
    1. Valid OKF YAML-frontmatter (`type: Task Package`, `status`, `title`, `generated`).
    2. Eksistensen af sektionen `## 🎯 Formål` (eller `## Purpose`).
    3. Eksistensen af eksekverbare acceptkriterier (`- [ ]`).
    4. Eksistensen af negative forretningsregler under `## 🚫 Must NOT`.
    5. At definitionerne i `CONTEXT.md` følger Aristoteles' formel (`**Term**:\n<Definition>\n_Avoid_: <synonymer>`).
  * *Håndhævelse i koden*: Returnerer exit-kode 1, hvis task-filen mangler, er fejlbehæftet eller overtræder formateringskravene.

#### 3. Implementering under Runtime Sandboxing (Værkstedet)
* **Type**: Metodisk TDD + Hård runtime-beskyttelse
* **Hvad der sker**: Koden skrives efter Red/Green TDD-princippet (først en fejlende test, derefter den minimale kode, der løser den, og til sidst refaktorisering).
* **Kontrolpunkt**: Gatekeeper Hook & Sandbox
  * *Hvem godkender*: Git/CLI-hooks (`gatekeeper.py`) og Linux Bubblewrap-sandbox (`sandbox.py`).
  * *Hvordan*: Agentens handlinger overvåges og begrænses under kørslen.
  * *Håndhævelse i koden*:
    * `gatekeeper.py` forhindrer workspace-escapes (stier uden for repo-roden) og blokerer modifikation af beskyttede stier (`src/`, `tests/`, `.github/` samt `.agents/` med undtagelse af `AGENTS.md`), hvis der ikke findes en aktiv task i `tasks/`.
    * Destruktive kommandoer som `git push` og `git reset --hard` blokeres hårdt.
    * Bubblewrap-sandboxen isolerer processer via Linux namespaces (`--unshare-pid`, `--unshare-net`, `--ro-bind`).
  * *Bemærk om TDD*: Selve rækkefølgen (Red før Green) registreres ikke historisk af test-runneren; det er en metodisk adfærd instrueret via agent-skills.

#### 4. Flerlags Verifikation
* **Type**: Hård software-gate
* **Hvad der sker**: Fuld automatisk eksekvering af projektets test- og analysesuiter samt generering af verifikationsrapporter.
* **Kontrolpunkt**: Diagnostic Engine (`agent-gauntlet verify`)
  * *Hvem godkender*: Verifikationsmotoren (`features/evidence/verifier.py`).
  * *Hvordan*: Runneren eksekverer de lag, der er defineret i `gauntlet.toml`:
    * **Types**: Typechecker (f.eks. `pyright`, `mypy` eller `tsc`).
    * **Linters**: Lint-regler og formatering (f.eks. `ruff`, `eslint`, `clippy`).
    * **Tests**: Enhedstests og integrationstests.
    * **Invarianter & Mutationer**: Mutations- og invarianttjek (`mutants.py`, `hypothesis`, `stryker`).
  * *Håndhævelse i koden*: Alle diagnostiske lag skal melde fejlfri kørsel (`PASSED`). Ved succes genereres automatisk `verification-report.json`, `evidence.json` og `evidence.md` med deterministiske SHA-256 digests over kildetræ (`source_manifest_digest`), konfiguration, opgave og politikker.

#### 5. Review mod Kodestandarder
* **Type**: Hybrid gate (Agent Skill + Udvikleraccept)
* **Hvad der sker**: Den implementerede løsning auditeres mod arkitekturretningslinjer og regler i `CODING_STANDARDS.md`.
* **Kontrolpunkt**: Standards Review (`code-review` skill)
  * *Hvem godkender*: Udvikleren assisteret af agentens review-skill.
  * *Hvordan*: Agenten gennemgår diff'en op mod kodestandarderne og fremhæver eventuelle arkitekturbrud, manglende fejlhåndtering eller navngivningsfejl.
  * *Håndhævelse i koden*: Gaten er procesmæssig og beror på agentens review-rapport kombineret med udviklerens godkendelse.

#### 6. Drift- og Integritetskontrol (Two-Tier Model)
* **Type**: Hård software-gate
* **Hvad der sker**: Verificering af, at kildekoden og arbejdstræet ikke er blevet manipuleret eller er driftet efter testkørslen.
* **Kontrolpunkt**: Drift Verification (`agent-gauntlet check-evidence`)
  * *Hvem godkender*: `execute_check_evidence` i `verifier.py`.
  * *Hvordan*: Værktøjet genberegner det aktuelle kildetræs workspace-manifest og sammenligner det direkte med værdierne i `verification-report.json`.
  * *Håndhævelse i koden*:
    * **Tier 1 (Lokal drift-kontrol)**: Er blot én byte ændret efter `verify`, afvises tjekket med fejl. Lokale HMAC-nøgler er udfaset jf. [ADR 0005](docs/adr/0005-two-tier-verification-and-attestation-model.md), og ældre HMAC-beviser afvises eksplicit.
    * **Tier 2 (Attestation i CI)**: I beskyttede CI-miljøer genereres en kryptografisk DSSE-attest (Sigstore/OIDC) via `attestation.py`, som verificeres af `agent-gauntlet check-attestation` op mod en defineret `trust-policy.json`.

#### 7. Release Readiness
* **Type**: Hård software-gate
* **Hvad der sker**: Koden klargøres til release og merge ved at kontrollere synkronisering mellem versioner, ændringslog og dokumentation.
* **Kontrolpunkt**: Release Gate (`agent-gauntlet check-release`)
  * *Hvem godkender*: Release-verifieren (`features/evidence/release_gate.py`).
  * *Hvordan*: Værktøjet udfører tre specifikke tjek:
    1. **Versionskonsistens**: Versionsnumre skal matche på tværs af projektets manifests (`pyproject.toml`, `package.json`, `Cargo.toml`).
    2. **Changelog-synkronisering**: `CHANGELOG.md` skal indeholde et afsnit for den pågældende version.
    3. **ADR-referencer**: Samtlige ADR-filer i `docs/adr/` skal være eksplicit refereret eller linket i enten `README.md` eller `spec.md`.
  * *Håndhævelse i koden*: Returnerer exit-kode 1, hvis der er uoverensstemmelse i versionsnumre, manglende changelog-sektion eller forældreløse ADR-dokumenter.
  * *Praktisk udviklerflag*: Med flaget `--allow-unreleased` tillader værktøjet sektionen `[Unreleased]` i `CHANGELOG.md` under løbende udvikling og lokale tests forud for den endelige versions-tagging.

### 👥 De 4 AI-roller & Session Handoff

For at undgå uendelige review-loops (*bikeshedding*) og bevare et skarpt kontekstvindue, udleder `agent-gauntlet` automatisk den næste ingeniør-rolle via `infer_next_session_role()`:

1. **`Senior Software Engineer (System Architecture & Requirements)`**:
   * Aktiveres ved nye eller `DRAFT`-opgaver. Udfordrer antagelser, definerer negative invarianter (`## 🚫 Must NOT`) og eksekverbare kriterier forud for kodning via `agent-gauntlet check-spec`.
2. **`Senior Software Engineer (Feature Implementation & Testing)`**:
   * Aktiveres ved `ACTIVE`-opgaver med udestående kriterier. Driver TDD-cyklussen (`RED` $\to$ `GREEN` $\to$ `REFACTOR`) og forsegler evidens via `agent-gauntlet verify`.
3. **`Senior Software Engineer (Independent Code Review & Audit)`**:
   * Tager over i en frisk session, når opgaven består. Udfører to-akset granskning langs **Akse A (Standarder)** jf. `CODING_STANDARDS.md` og **Akse B (Krav)** jf. `spec.md`/`tasks/`.
4. **`Release & Operations Engineer (Release Attestation & Deployment)`**:
   * Tager over når alle opgaver og audits er godkendt. Kører `agent-gauntlet check-release`, forbereder versionsbump og klargør release.

### 📋 Centrale Artefakter: Oprettelse og Formål

| Artefakt | Primær placering | Hvordan det oprettes | Formål og funktion |
|---|---|---|---|
| **`gauntlet.toml`** | Rodmappen | Scaffoldes via `ProjectScaffolder` under `agent-gauntlet init`. | Værktøjskonfiguration. Styrer hvilke analyse- og testlag `agent-gauntlet verify` eksekverer samt grænseværdier. |
| **`tasks/*.md`** | Mappen `tasks/` | Oprettes manuelt eller via skabelon for hver opgave. | Formel opgavebinding. Definerer opgavens OKF-metadata, formål, acceptkriterier (`- [ ]`) og negative regler (`## 🚫 Must NOT`). Valideres af `check-spec`. |
| **`CONTEXT.md`** | Rodmappen | Oprettes ved init og opdateres under idéafklaring. | Domænekontekst og glossar. Indeholder forretningsmål og et definitionsglossar, der valideres af `check-spec` efter Aristoteles' formel. |
| **`CODING_STANDARDS.md`** | Rodmappen | Genereres stack-specifikt ved init via `scaffolder.py`. | Kodestandarder. Beskriver arkitekturmønstre, navnekonventioner og koderegler, som anvendes under `code-review`. |
| **`verification-report.json` / `evidence.json`** | Rodmappen | Genereres maskinelt ved kørsel af `agent-gauntlet verify`. | Verifikations- og evidensrapport. Indeholder testresultater og deterministiske SHA-256 digests over kildekoden (`source_manifest_digest`), konfiguration og tasks. Kontrolleres mod drift af `check-evidence`. |
| **`spec.md`** | Rodmappen | Forfattes af udvikler/arkitekt. | Systemkontrakter. Overordnet teknisk specifikation, som agenten navigerer efter, og som tjekkes for ADR-referencer af `check-release`. |
| **`docs/adr/*.md`** | Mappen `docs/adr/` | Oprettes ved arkitekturvalg via skabelon. | Architecture Decision Records (ADR). Dokumenterer historiske og nye tekniske valg. `check-release` håndhæver, at alle ADR'er linkes i `README.md` eller `spec.md`. |

---

## 🎯 Arkitektur & Designprincipper

1. **Uncle Bob Clean Architecture & TDD:**
   * Forankret i de 3 Love for TDD, Transformation Priority Premise (TPP) og Single Responsibility Principle (SRP).
2. **Package-by-Feature Struktur (Screaming Architecture):**
   * Hver komponent er isoleret i en feature-underpakke med høj sammenhørighed og lav kobling ([ADR 0001](docs/adr/0001-package-by-feature-architecture.md)).
3. **Multi-Stack Support (Tier-1):**
   * 🐍 **Python**: `ruff`, `pyright`/`mypy`, `pytest`/`unittest`, `hypothesis`, `mutants.py`/`mutmut`.
   * 🌐 **TypeScript / Node**: `eslint`/`biome`, `tsc --noEmit`, `vitest`/`jest`, `fast-check`, `stryker`.
   * 🦀 **Rust**: `cargo clippy`, `cargo check`, `cargo test`, `proptest`, `cargo-mutants`.
4. **Actionable Diagnostics Engine:**
   * Omsætter rå fejludskrifter til strukturerede diagnoser med filstier, linjenumre og præcise udbedringsforslag (`remediation_hint`).
5. **Three-Tier Evidens & Tillidsmodel ([ADR 0005](docs/adr/0005-two-tier-verification-and-attestation-model.md) & [ADR 0007](docs/adr/0007-local-transparent-supervisor-and-wasm-verifier.md)):**
   * `LOCAL_UNSUPERVISED`: Hurtig lokal feedback og usigneret rapport til kooperativ drift-kontrol.
   * `LOCAL_SUPERVISED`: Signeret lokal verifikationsrapport udstedt af en privilegie-adskilt supervisor med efemere task-certifikater og hash-kædede session logs.
   * `CI_ATTESTED`: Uafhængig, kryptografisk Sigstore OIDC keyless DSSE/in-toto attestering i privilegerede CI-workflows.
6. **Lokal Transparent Supervisor & WASM Verifier ([ADR 0007](docs/adr/0007-local-transparent-supervisor-and-wasm-verifier.md)):**
   * **Nul Ambient Authority WASM Kerne**: Deterministisk evaluering af agentens handlinger (`wit/gauntlet_policy.wit`) uden filsystem-, netværks- eller procesadgang.
   * **Linux Systemd Socket Activation**: On-demand start via `agent-gauntlet.socket` uden behov for permanente baggrundsterminaler.
   * **Bubblewrap (`bwrap`) Isolation**: Kører verifikation mod et frosset, deterministisk workspace-snapshot uden netværksadgang.
   * **Beskyttet Nøglehåndtering**: Private nøgler opbevares udelukkende af supervisoren uden for projektets workspace (`~/.agent-gauntlet/supervisor/` med `0700`/`0600` rettigheder).

---

## 🏗️ Mappestruktur (`Package-by-Feature`)

```text
agent-gauntlet/
├── tasks/                        # Aktive og afsluttede opgavepakker (OKF v0.2)
├── docs/adr/                     # Arkitekturbeslutninger (ADRs 0001-0007)
├── CONTEXT.md                    # Domæne-glossary (Aristoteles' genus et differentiam)
├── CODING_STANDARDS.md           # Multi-stack kodestandarder (Python, TS, Rust, Go, Web)
├── spec.md                       # Makro-specifikation & system-invarianter
├── CHANGELOG.md                  # Versionshistorik & release notes (Keep a Changelog)
├── ROADMAP.md                    # Prioriteret feature-køreplan & udvidelser
├── gauntlet.toml                 # Deklarativ multi-stack konfiguration
├── wit/                          # WebAssembly Interface Types (WIT) specifikationer
├── crates/                       # Rust WebAssembly policy component source
├── packages/agent-gauntlet/      # NPM / NPX distributions-pakke & bin/agent-gauntlet.js wrapper
├── plugins/agent-gauntlet/       # Antigravity plugin & skills (old-coder, grill-me, code-review, diagnose)
├── src/agent_gauntlet/
│   ├── __init__.py
│   ├── cli.py                    # Udvidet CLI (init, verify, check-evidence, check-attestation, okf)
│   └── features/
│       ├── adapters/             # Vertikale feature-slices for AI-harnesses (Antigravity shim, Claude mv.)
│       ├── supervisor/           # Lokal privilege-separated supervisor, FSM, event log & platform seams
│       │   ├── core/             # Portabel forretningslogik, FSM, modeller, snapshot, seams, engine
│       │   ├── wasm/             # WebAssembly component verifier & host integration
│       │   └── platform/linux/   # Linux systemd socket activation, Unix socket, bwrap & key provider
│       ├── config/               # gauntlet.toml / gauntlet.json loader & schema
│       ├── diagnostics/          # Actionable LLM feedback engine & extractors
│       ├── evidence/             # Canonical manifest, verification report, attestation & trust policy
│       ├── gauntlet/             # Multi-layer runner & timeout kontrol
│       ├── hooks/                # Pre-invocation policy engine gatekeeper
│       ├── okf/                  # OKF v0.2 metadata parsing, validering & stempling
│       ├── scaffold/             # Ikke-destruktiv bootstrap motor
│       └── stacks/               # Auto-detektor & standardprofiler (Python, TS, Rust)
└── tests/features/               # 1:1 testsymmetri mod features (inkl. tests/features/supervisor/)
```

---

## 🛠️ Fuld CLI Reference

### 1. Initialiser Workspace (`init`)
Klargør lynhurtigt et nyt eller eksisterende projekt med fuld scaffolding:

```bash
# Standard auto-detektering af stack
agent-gauntlet init

# Eksplicit valg af stack og konfigurationsformat
agent-gauntlet init --stack typescript
agent-gauntlet init --stack rust --format json

# Tving overskrivning af eksisterende skabeloner
agent-gauntlet init --force
```

### 2. Kør Verifikations-Gauntlet (`verify`)
Kør alle konfigurerede lag, udtræk actionable diagnostics og generer en usigneret eller supervisor-signeret verifikationsrapport (`verification-report.json` v2.0 og `evidence.md`):

```bash
# Standard kørsel bundet til en opgave
agent-gauntlet verify --task-id 001-bootstrap

# Returner struktureret JSON med actionable diagnostics til LLM / AI-agenter
agent-gauntlet verify --diagnostics-json

# Kør mod en specifik testfil / mål (markerer kørslen PARTIAL for at forhindre for tidlig stabilisering)
agent-gauntlet verify --test-target tests.features.test_gauntlet
```

Når gauntlettet passerer, beregner `agent-gauntlet` automatisk et deterministisk `CanonicalWorkspaceManifest` (pre og post testkørsel), genererer `verification-report.json` og opdaterer `evidence.md`.

### 3. Validering af Evidens & Drift-kontrol (`check-evidence`)
Verificerer at det aktuelle kildetræ matcher den lokale verifikationsrapport, og at alle påkrævede tjek bestod:

```bash
agent-gauntlet check-evidence
```

**Output eksempler:**
* **Gyldig kildetilstand:**
  ```text
  [VALID] Source manifest verified (46970990edf43304) [origin: LOCAL, attestation: ABSENT].
  ```
* **Kildekode ændret efter verifikation (Drift):**
  ```text
  FAILED: Source manifest drift detected! Report bound to '46970990edf43304', but current workspace is '7c12f00a...'.
  ```

### 4. Attesteringsvalidering & Release Gate (`check-attestation`)
Validerer uafhængige, detached Sigstore / GitHub OIDC attestationsbundter mod en defineret tillidspolitik ([ADR 0005](docs/adr/0005-two-tier-verification-and-attestation-model.md)):

```bash
# Valider rapport og attestering
agent-gauntlet check-attestation --attestation attestation.bundle --trust-policy .agent-gauntlet/trust-policy.json

# Advisory-mode for lokale uattesterede kendsgerninger
agent-gauntlet check-attestation --allow-unattested
```

### 5. Release Readiness & Dokumentations-Synkronisering (`check-release`)
Mekanisk validering af versionsharmoni og dokumentation før release:

```bash
# Valider at pyproject.toml, package.json, CHANGELOG.md og docs/adr/ er 100% synkroniserede
agent-gauntlet check-release

# Output resultater som struktureret JSON
agent-gauntlet check-release --json

# Tillad [Unreleased] sektion under aktiv udvikling
agent-gauntlet check-release --allow-unreleased
```

### 6. Early-Phase Spec & Business Rules Gatekeeper (`check-spec`)
Mekanisk validering af at opgavespecifikationer indeholder eksplicitte forretningsinvarianter (`Must NOT`), eksekverbare acceptkriterier og overholder [CONTEXT.md](CONTEXT.md) ordbogsformatet før kodning påbegyndes:

```bash
# Valider aktiv opgave eller seneste opgave i tasks/
agent-gauntlet check-spec

# Valider en specifik opgave
agent-gauntlet check-spec -t 039-early-phase-specification-and-business-rules-gatekeeper

# Valider samtlige opgaver i tasks/
agent-gauntlet check-spec --all

# Output resultater som struktureret JSON
agent-gauntlet check-spec --json
```

### 7. OKF Metadata Validering (`okf validate`)
Validerer Open Knowledge Format (OKF v0.2) overensstemmelse for Markdown-dokumenter:

```bash
agent-gauntlet okf validate
# Validerer frontmatter-skemaer, aktører og temporale invarianter (t_verified >= t_generated)
```

### 8. Supervisor Daemon & WebAssembly Evaluator (`supervisor`)
Håndter og inspicer den lokale privilege-adskilte supervisor daemon:

```bash
# Start supervisoren som baggrundstjeneste (aktiverer WASM evaluering og Unix socket)
agent-gauntlet supervisor start --daemon

# Vis supervisor status, aktiv socket og installationsnøgle
agent-gauntlet supervisor status
```

### 9. Workspace Diagnostic & Multi-Stack Integrity (`doctor`)
Undersøg workspace-konfiguration, stakke og miljøforudsætninger:

```bash
# Udfør fuld sundhedsdiagnostik (Node.js, TypeScript Project References, Cargo overvågning, Systemd)
agent-gauntlet doctor
```

---

## 💻 Python API

Du kan også integrere `agent-gauntlet` direkte i dine egne Python test-runners eller agent-workflows:

```python
from pathlib import Path
from agent_gauntlet.features.config import load_config
from agent_gauntlet.features.gauntlet import run_gauntlet
from agent_gauntlet.features.evidence import (
    VerificationReportEngine,
    compute_workspace_manifest,
    TrustPolicyEngine,
)
from agent_gauntlet.features.evidence.verifier import execute_verify

# 1. Kør programmatisk verifikation bundet til en task
exit_code = execute_verify(workspace=Path("."), task_id="001-bootstrap")

# 2. Beregn deterministisk kildemanifest (multi-digest over workspace)
manifest = compute_workspace_manifest(Path("."))
print(f"Source manifest digest: {manifest.source_manifest_digest[:16]}")

# 3. Indlæs verifikationsrapport og evaluer mod tillidspolitik
report_file = Path("verification-report.json")
if report_file.is_file():
    engine = VerificationReportEngine()
    report = engine.load_report_json(report_file.read_text(encoding="utf-8"))

    trust_engine = TrustPolicyEngine()
    policy = trust_engine.load_policy({})
    decision = trust_engine.evaluate(report, attestation=None, policy=policy)
    print(f"Release eligible: {decision.release_eligible}")
```

---

## 🧪 Verifikation & Gauntlet Test

Kør hele verifikationskæden med 100% mutationsdrab og negative controls:

```bash
sh tools/gauntlet.sh
```

---

## 🗺️ Arkitektur (ADRs)

Projektets invariante tekniske valg og designprincipper er dokumenteret som uforanderlige Architecture Decision Records i [`docs/adr/`](docs/adr/):
- 🏛️ **[ADR 0001](docs/adr/0001-package-by-feature-architecture.md)**: Package-by-Feature / Screaming Architecture
- 🏛️ **[ADR 0002](docs/adr/0002-cryptographic-evidence-authority.md)**: Cryptographic Evidence Authority
- 🏛️ **[ADR 0003](docs/adr/0003-surgical-gatekeeper-and-no-remote-push.md)**: Surgical Gatekeeper and No Remote Push
- 🏛️ **[ADR 0004](docs/adr/0004-harness-adapter-slices.md)**: Harness Adapter Slices
- 🏛️ **[ADR 0005](docs/adr/0005-two-tier-verification-and-attestation-model.md)**: Two-Tier Verification and Attestation Model
- 🏛️ **[ADR 0006](docs/adr/0006-multi-harness-policy-adapter-contract.md)**: Multi-Harness Policy Adapter Contract
- 🏛️ **[ADR 0007](docs/adr/0007-local-transparent-supervisor-and-wasm-verifier.md)**: Local Transparent Supervisor and WASM Verifier

## 🗺️ Roadmap

- 🗺️ **[ROADMAP.md](ROADMAP.md)**: Prioriteret oversigt over fremtidige features (Multi-Harness integration, Changed-Line Differential Coverage, Fresh-Context Adversarial Verifier m.fl.).

---

## 🙏 Anerkendelse & Inspiration (Credits)

`agent-gauntlet` bygger videre på idéer, historiske rødder og pionerarbejde inden for stringent verifikation:

- **[Jost Amman (1564)](https://en.wikipedia.org/wiki/Jost_Amman)**: For den historiske illustration af *Spiessgasse* (*[Running the Gauntlet](https://en.wikipedia.org/wiki/Running_the_gauntlet)*, *Kriegs Ordnung*), der symboliserer at lade koden løbe igennem en uomgængelig række af spyd (linters, typer, tests, invarianter og mutationer).
- **[Robert C. Martin ("Uncle Bob")](https://x.com/unclebobmartin/status/2080257779395154409)**: For den oprindelige idé om at erstatte manuel kodeinspektion med en uomgængelig *gauntlet* af tests, typer, mutation testing og invarianter.
- **[amazingang (old-coder)](https://github.com/amazingang/old-coder)**: For formuleringen af Evidence-First filosofien (*"Trust moves from inspection to constraints"*).
- **[Matt Pocock](https://github.com/mattpocock)**: For skabelsen af workflow-skills (`grill-me`, `grill-with-docs`, `diagnose`, `code-review` m.fl.), som muliggør sokratisk kravsafklaring, domæneforankring og uafhængig to-akset kode-granskning.


