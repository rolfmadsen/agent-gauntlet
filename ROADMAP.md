# Agent-Gauntlet Roadmap & Fremtidige Udvidelser

Dette dokument samler og prioriterer fremtidige udvidelser og modenheds-features for `agent-gauntlet`, destilleret fra referencedokumenterne i [`old-coder/skills/old-coder/references/`](../old-coder/skills/old-coder/references/).

---

## 🗺️ Prioriteret Feature Oversigt

| # | Feature | Formål | Kilde / Reference | Prioritet |
|---|---|---|---|:---:|
| 1 | **Fresh-Context Adversarial Verifier** | Uafhængig sub-agent i ren session, der blindt angriber koden for blinde vinkler, test-gaming og spec-drift | [`verifier.md`](../old-coder/skills/old-coder/references/verifier.md), [`verifier-case-study.md`](../old-coder/skills/old-coder/references/verifier-case-study.md) | **HØJ** |
| 2 | **Changed-Line Differential Coverage** | Gennemtvinger 100% test- og forgreningstjek på *udelukkende* ændrede/tilføjede linjer i git diff | [`gauntlet.md`](../old-coder/skills/old-coder/references/gauntlet.md) | **HØJ** |
| 3 | **Spec $\to$ Test Mapping & "Must NOT" Validator** | Mekanisk 1:1 håndhævelse af at alle Gherkin-scenarier og negative begrænsninger ("Must NOT") har specifikke tests | [`templates.md`](../old-coder/skills/old-coder/references/templates.md) | **MEDIUM** |
| 4 | **Extended Security & Supply-Chain Audits** | Automatiserede gauntlet-lag for `secret-scan` (`gitleaks`) og pakkesårbarheder (`pip-audit`, `npm audit`, `cargo-audit`) | [`gauntlet.md`](../old-coder/skills/old-coder/references/gauntlet.md) | **MEDIUM** |
| 5 | **Suite Health & Test-Order Randomizer** | Randomiseret testrækkefølge med deterministisk seed for at afsløre globale tilstandslækager og flakiness | [`gauntlet.md`](../old-coder/skills/old-coder/references/gauntlet.md) | **LAV** |

---

## 🔍 Detaljerede Feature Beskrivelser

### 1. 🕵️ Fresh-Context Adversarial Verifier Protocol (`agent-gauntlet verifier`)
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

### 2. 🎯 Changed-Line Differential Coverage (`diff-cover`)
* **Koncept**:
  Et præcisions-verifikationslag, der isolerer den aktuelle Git-diff og beregner testdækning for kun de linjer, der er rørt ved i opgaven.
* **Hvorfor det er vigtigt**:
  * Tvinger 100% test- og branch-dækning på al ny kode og bugfixes.
  * Realistisk i eksisterende, store kodebaser: Projektet behøver ikke have 100% total dækning for at nye ændringer er højt verificerede.

---

### 3. 📋 Mekanisk Spec $\to$ Test Mapping & "Must NOT" Invariant Validator
* **Koncept**:
  En parser der forbinder hvert enkelt scenarie i opgaven samt hver negative begrænsning ("Must NOT") direkte med specifikke testmetoder (`test_file.py::test_scenario_name`).
* **Hvorfor det er vigtigt**:
  * Forhindrer agenten i at springe ubehagelige fejltilfælde eller negative sikkerhedskrav over.
  * Gør `evidence.md` tabellen fuldstændig mekanisk verificerbar uden menneskelig gætteleg.

---

### 4. 🔒 Extended Security & Supply-Chain Audit Layers
* **Koncept**:
  Indbygge valgfrie plug-and-play gauntlet-lag til:
  * `secret-scan`: Forhindrer at nøgler, tokens eller passwords begås i koden (via `gitleaks`).
  * `pkg-audit`: Validerer at nyindførte afhængigheder ikke indeholder kendte CVE'er (via `pip-audit`, `npm audit`, `cargo-audit`).
  * `capability-diff`: Sikrer at agenten ikke utilsigtet introducerer nye netværks- eller procesrettigheder i koden.

---

### 5. 🎲 Suite Health & Test-Order Randomizer
* **Koncept**:
  Køre testsuiterne i randomiseret rækkefølge med fast seed (`pytest-randomly`, `vitest --sequence.shuffle`, `go test -shuffle=on`).
* **Hvorfor det er vigtigt**:
  * Opdager hvis tests i virkeligheden deler tilstand (f.eks. efterladte database-rækker, singleton-mutationer, globale mocks) og kun består, fordi de køres i en bestemt rækkefølge.

---

## 📅 Næste Skridt
Når udviklingen genoptages, kan en ny opgave oprettes i `tasks/` med udgangspunkt i én af ovenstående 5 features (f.eks. `tasks/005-adversarial-verifier-protocol.md` eller `tasks/005-changed-line-coverage.md`).
