# agent-gauntlet 🛡️

[![CI](https://github.com/rolfmadsen/agent-gauntlet/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/rolfmadsen/agent-gauntlet/actions/workflows/ci.yml)
[![Mutants Killed](https://img.shields.io/badge/mutants%20killed-100%25-brightgreen.svg)](tools/mutants.py)
[![Evidence Model](https://img.shields.io/badge/evidence-Two--Tier%20Attestation-blue.svg)](docs/adr/0005-two-tier-verification-and-attestation-model.md)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**agent-gauntlet** er en universel multi-stack verifikations- og actionable diagnostics motor bygget på **Uncle Bobs (Robert C. Martin) TDD- og Clean Craftsmanship-filosofi**.

Den omgiver AI-genereret kode med et kompromisløst verifikations-gauntlet (Linters, Type-checkere, Unit tests, Property- og Invariant-tests, Mutationsafprøvning og To-Tier evidens & attestering jf. [ADR 0005](docs/adr/0005-two-tier-verification-and-attestation-model.md)) og oversætter rå fejludskrifter til **Actionable Diagnostics**, som AI-agenter kan handle direkte på.

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
5. **Two-Tier Evidens & Tillidsmodel ([ADR 0005](docs/adr/0005-two-tier-verification-and-attestation-model.md)):**
   * Deterministisk `CanonicalWorkspaceManifest` med symlink-flugtbeskyttelse og usignerede `verification-report.json` rapporter til lokal drift-kontrol kombineret med uafhængig, kryptografisk Sigstore OIDC attestering i CI.

---

## 🧭 Hvordan virker agent-gauntlet? (Core Loop)

`agent-gauntlet` tvinger AI-agenten igennem en deterministisk, videnskabelig udviklingsproces, hvor påstande erstattes af eksekverbare beviser:

```mermaid
flowchart TD
    subgraph 1. Forberedelse & Intent
        Intent["🎯 1. SPEC & Intent Afklaring\n(spec.md / CONTEXT.md)"] --> Appr["👤 2. Menneskelig Godkendelse\n(Gennemgå og frys specifikationen)"]
    end

    subgraph 2. Uncle Bob TDD-Cyklus
        Appr --> Red["🔴 3. RED: Skriv fejlet test\n(Bevis at testen rent faktisk fejler)"]
        Red --> Green["🟢 4. GREEN: Minimal kode\n(Få testen til at passere)"]
        Green --> Refactor["🔵 5. REFACTOR: Oprydning\n(Bevar grøn status)"]
    end

    subgraph 3. Multi-Layer Gauntlet
        Refactor --> Layer1["🔍 Lag 1: Linter (Ruff / ESLint / Clippy)"]
        Layer1 --> Layer2["📐 Lag 2: Types (Pyright / Mypy / tsc)"]
        Layer2 --> Layer3["🧪 Lag 3: Unit Tests (pytest / unittest / vitest)"]
        Layer3 --> Layer4["🎲 Lag 4: Invarianter (Hypothesis / Proptest)"]
        Layer4 --> Layer5["🧬 Lag 5: Mutations Gauntlet (mutants.py)"]
    end

    subgraph 4. Feedback & Two-Tier Evidens
        Layer1 -. Fejl .-> Diag["⚙️ Actionable Diagnostics Engine\n(Parser fil, linje og udbedringsforslag)"]
        Layer2 -. Fejl .-> Diag
        Layer3 -. Fejl .-> Diag
        Layer4 -. Fejl .-> Diag
        Layer5 -. Fejl .-> Diag
        Diag --> FixLoop["🔄 Autonomt Fixer-Loop\n(Fokuseret intervention)"]
        FixLoop --> Red

        Layer5 -->|Alle lag PASSED| Report["📋 6. Lokal Verifikationsrapport\n(Canonical Workspace Digest + Unsigned Report)"]
        Report --> Ledger["📄 verification-report.json & evidence.md"]
        Ledger -. CI Push / Release .-> Attest["🔏 7. Sigstore OIDC Attestation\n(actions/attest keyless DSSE bundle)"]
    end
```

### De 4 Nøglesøjler i Kredsløbet:
1. **SPEC & Intent Afklaring:** Formålet fastlægges entydigt i `spec.md` forankret i domænets sprog (`CONTEXT.md`).
2. **TDD Disciplin (Red $\to$ Green $\to$ Refactor):** Ingen kode skrives uden en forudgående, verificeret rød test.
3. **Kompromisløst Gauntlet:** Koden skal overleve 5 uafhængige kontrol-lag inkl. syntetiske mutanter og tilfældige kanttilfælde.
4. **Actionable Diagnostics & Two-Tier Evidens:** Hvis et lag fejler, modtager agenten præcise maskinlæsbare udbedringsforslag. Når alt er grønt, udregnes et deterministisk kildemanifest til lokal drift-kontrol, og der genereres en uafhængig Sigstore OIDC attestering i CI.

---

## 🏗️ Mappestruktur (`Package-by-Feature`)

```text
agent-gauntlet/
├── tasks/                        # Aktive og afsluttede opgaver (rene handoffs)
├── docs/adr/                     # Arkitekturbeslutninger (ADRs)
├── CONTEXT.md                    # Domæne-glossary (Aristoteles' genus et differentiam)
├── ROADMAP.md                    # Prioriteret feature-køreplan & udvidelser
├── gauntlet.toml                 # Deklarativ multi-stack konfiguration
├── plugins/agent-gauntlet/       # Antigravity IDE plugin & skills (grill-me, diagnose)
├── src/agent_gauntlet/
│   ├── __init__.py
│   ├── cli.py                    # Udvidet CLI (init, verify, check-evidence, check-attestation, okf)
│   └── features/
│       ├── adapters/             # Vertikale feature-slices for AI-harnesses (Antigravity mv.)
│       ├── config/               # gauntlet.toml / gauntlet.json loader & schema
│       ├── diagnostics/          # Actionable LLM feedback engine & extractors
│       ├── evidence/             # Canonical manifest, verification report, attestation & trust policy
│       ├── gauntlet/             # Multi-layer runner & timeout kontrol
│       ├── hooks/                # Pre-invocation policy engine gatekeeper
│       ├── okf/                  # OKF v0.2 metadata parsing, validering & stempling
│       ├── scaffold/             # Ikke-destruktiv bootstrap motor
│       └── stacks/               # Auto-detektor & standardprofiler (Python, TS, Rust)
└── tests/features/               # 1:1 testsymmetri mod features
```

---

## 🚀 Hurtig Start & Anvendelse

### 1. Installer CLI-værktøjet (Engangs-opsætning)
Installer `agent-gauntlet` globalt eller i dit foretrukne Python-miljø:

```bash
# Klon og installer i editable tilstand
git clone https://github.com/rolfmadsen/agent-gauntlet.git ~/Github/agent-gauntlet
pip install -e ~/Github/agent-gauntlet
```

---

### 2. Initialiser i dit Projekt (⭐ Anbefalet Standard & Best Practice)
For at sikre at regler ([.agents/AGENTS.md](.agents/AGENTS.md)), begreber ([CONTEXT.md](CONTEXT.md)), Architecture Decision Records (ADR) ([docs/adr/](docs/adr/)) og verifikationskrav ([gauntlet.toml](gauntlet.toml) & [tasks/](tasks/)) **følger din kildekode i Git**, initialiseres `agent-gauntlet` direkte i projektets rodmappe:

```bash
cd /sti/til/dit-projekt

# Auto-detekter stack (Python, TypeScript, Rust, Go) og scaffold projektet sikkert
agent-gauntlet init
```

#### 📦 Hvad `agent-gauntlet init` opretter i projektet:
| Fil / Mappe | Formål |
|---|---|
| [`gauntlet.toml`](gauntlet.toml) | Deklarativ konfiguration af linter, types, tests, mutation testing |
| [`CONTEXT.md`](CONTEXT.md) | Domæne-glossary for projektet (Aristoteles' genus et differentiam) |
| [`tasks/001-bootstrap.md`](tasks/) | Opgavemappe til håndhævelse af task-kontrakter & acceptkriterier |
| [`docs/adr/`](docs/adr/) | Architecture Decision Records (ADR) til projekt-specifikke beslutninger |
| [`.agents/AGENTS.md`](.agents/AGENTS.md) | AI-agent retningslinjer, Response HUD og task-management protokoller |
| [`.agents/hooks.json`](.agents/hooks.json) | Pre-Invocation Hook til Stop/Go gatekeeperen |
| [`.agents/skills/`](.agents/skills/) | Bundled skills (`old-coder`, `grill-me`, `grill-with-docs`, `diagnose`) |

> [!TIP]
> **🛡️ Ikke-destruktiv garanti (Safety First):**  
> `agent-gauntlet init` overskriver **aldrig** eksisterende filer i dit projekt, medmindre du udtrykkeligt angiver `--force`.

> [!IMPORTANT]
> **🚪 Zero Lock-in & Hurtig Afinstallation (Clean Uninstall):**  
> Hvis du fortryder eller vil fjerne `agent-gauntlet` fra et projekt, slettes de oprettede metadata-filer med én linje uden at røre ved projektets egen kildekode:
> ```bash
> rm -rf .agents tasks docs/adr CONTEXT.md gauntlet.toml evidence.json evidence.md
> ```

---

### 3. Valgfrit: Global Antigravity Plugin Installation
Hvis du ønsker at have adgang til `agent-gauntlet` skills (`/grill-me`, `/diagnose`, osv.) på tværs af **alle** workspaces i Google Antigravity IDE — også i projekter hvor du endnu ikke har kørt `agent-gauntlet init` — kan du registrere pluginet globalt:

```bash
mkdir -p ~/.gemini/config/plugins/
cp -r ~/Github/agent-gauntlet/plugins/agent-gauntlet ~/.gemini/config/plugins/
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
Kør alle konfigurerede lag, udtræk actionable diagnostics og generer en usigneret verifikationsrapport (`verification-report.json` v2.0 og `evidence.md`):

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

### 5. OKF Metadata Validering (`okf validate`)
Validerer Open Knowledge Format (OKF v0.2) overensstemmelse for Markdown-dokumenter:

```bash
agent-gauntlet okf validate
# Validerer frontmatter-skemaer, aktører og temporale invarianter (t_verified >= t_generated)
```

---

## 💻 Python API

Du kan også integrere `agent-gauntlet` direkte i dine egne Python test-runners eller agent-workflows:

```python
from agent_gauntlet.features.gauntlet import run_gauntlet
from agent_gauntlet.features.config import load_config
from agent_gauntlet.features.evidence import (
    CanonicalWorkspaceManifest,
    VerificationReportEngine,
    TrustPolicy,
    evaluate_trust_policy,
)

# 1. Indlæs konfiguration og kør gauntlet
config = load_config(".")
layers = config.to_layer_definitions()
report = run_gauntlet(layers)

# 2. Beregn deterministisk kildemanifest
manifest = CanonicalWorkspaceManifest.compute(".")

# 3. Opret usigneret verifikationsrapport
engine = VerificationReportEngine()
verification_report = engine.create_report(
    task_id="task-001",
    task_title="Bootstrap",
    verdict="PASSED" if report.success else "FAILED",
    manifest_pre=manifest,
    manifest_post=manifest,
    layers=report.layers,
)

# 4. Evaluer tillidspolitik
policy = TrustPolicy.strict()
decision = evaluate_trust_policy(verification_report, attestation=None, policy=policy)
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

- 🏛️ **[docs/adr/](docs/adr/)**: Arkitekturbeslutninger (Architecture Decision Records) der fastlægger projektets invariante tekniske valg og designprincipper.

## 🗺️ Roadmap

- 🗺️ **[ROADMAP.md](ROADMAP.md)**: Prioriteret oversigt over fremtidige features (Multi-Harness integration, Changed-Line Differential Coverage, Fresh-Context Adversarial Verifier m.fl.).

---

## 🙏 Anerkendelse & Inspiration (Credits)

`agent-gauntlet` bygger videre på idéer og pionerarbejde inden for agentisk softwareudvikling:

- **[Matt Pocock](https://github.com/mattpocock)**: For skabelsen af workflow-skills (`grill-me`, `grill-with-docs`, `diagnose` m.fl.), som muliggør sokratisk kravsafklaring og domæneforankring.
- **[amazingang (old-coder)](https://github.com/amazingang/old-coder)**: For formuleringen af Evidence-First filosofien (*"Trust moves from inspection to constraints"*).
- **[Robert C. Martin ("Uncle Bob")](https://x.com/unclebobmartin/status/2080257779395154409)**: For den oprindelige idé om at erstatte manuel kodeinspektion med en uomgængelig *gauntlet* af tests, typer, mutation testing og invarianter.


