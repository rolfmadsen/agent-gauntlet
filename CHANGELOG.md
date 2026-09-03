# Changelog

All notable changes to the `agent-gauntlet` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.8.1] - 2026-09-03

### 🚀 Added
- **Context-Aware Smart Scaffolding & Non-Destructive Init (`Task 044`)**:
  - Prevented template pollution in mature workspaces: `agent-gauntlet init` now inspects `tasks/` and skips creating `001-bootstrap.md` when tasks already exist, and skips `0001-initial-architecture.md` when ADRs are already present.
  - Root `CODING_STANDARDS.md` updated to authoritative polyglot standards (Python, TypeScript, React, Rust, and Cross-Stack Boundary Invariants).
- **Native Rust Verification Layer & Doctor Detection**:
  - Added dedicated `rust` layer executing `cargo test` on `crates/gauntlet-policy-engine` to `gauntlet.toml`, `tools/gauntlet.sh` and pre-build checks.
  - Added unmonitored stack detection to `agent-gauntlet doctor` (`UNMONITORED_STACK`), ensuring workspaces with Rust crates (`Cargo.toml`) always have corresponding gauntlet layers.

---

## [0.8.0] - 2026-09-03

### 🚀 Added
- **Real WebAssembly Policy Engine & Local Transparent Supervisor Daemon (`Task 043`)**:
  - Standalone Rust WebAssembly policy engine (`crates/gauntlet-policy-engine`) compiled to `wasm32-unknown-unknown` and native shared library (`.so`), evaluating tool invocation policies in linear WebAssembly memory via Node.js V8 and ctypes.
  - Zero-dependency depth-aware top-level JSON parser in Rust preventing action spoofing through nested payload structures.
  - Cryptographic verification of WASM binaries using embedded SHA-256 digests with fail-closed defense against tampering (`WasmDigestMismatchError`).
  - Stdin streaming in WASM runner eliminating `ARG_MAX` limits and protecting code payloads from process table leaks.
  - Local transparent supervisor daemon (`agent-gauntlet supervisor start --daemon|status`) communicating over Unix Domain Sockets with systemd socket activation compatibility.
  - Re-entrant locking (`RLock`) in `SupervisorEngine` for race-free concurrent RPC execution.
  - Secure ephemeral key storage with `0700` POSIX directory isolation and per-session certificate issuance.
  - Transparent IDE hook integration for Google Antigravity with fail-closed security and stale socket fallback.

---

## [0.7.0] - 2026-08-31

### 🚀 Added
- **Polyglot Composite Coding Standards & Multi-Stack Detection (`Task 042`)**:
  - Recursive stack detector `detect_stacks()` scanning root and standard subdirectories (`frontend/`, `backend/`, `web/`, `api/`, `apps/*`, `packages/*`, `crates/*`, `wasm/`, `rust/`, `native/`, `src-wasm/`, `services/*`).
  - Modular composable coding standards generator (`src/agent_gauntlet/features/scaffold/standards.py`) synthesizing transversal engineering principles, idiomatic language standards (TypeScript/React, Python, Rust), and cross-stack boundary & interop invariants (OpenAPI, zero untyped JSON bridges, error envelopes).
  - Multi-stack scaffolding support (`--stacks typescript,python` / `--stack typescript,rust`) across `agent-gauntlet init`, `scaffold`, and `ProjectScaffolder`.
  - Added mutation testing coverage for polyglot composite generation and stack detection in `tools/mutants.py` (65/65 mutants killed).

---

## [0.6.0] - 2026-08-31


### 🚀 Added
- **Smart TypeScript Project References & Full Typecheck Detection (`Task 041`)**:
  - Comment- and trailing-comma-tolerant JSONC parser (`inspect_typescript_tsconfig`) for safe inspection of TypeScript configuration files.
  - Automatic detection of Project References / Solution Style tsconfigs (`tsconfig.app.json`, `tsconfig.node.json`, `"references": [...]`).
  - Dynamic generation of authoritative typecheck commands (`npx tsc -b` / `npx tsc --noEmit -p tsconfig.app.json`) in stack profiles, configuration loaders, and project scaffolding.
  - Doctor Integrity Check (`TSCONFIG_PROJECT_REFERENCES` warning) in `agent-gauntlet doctor` flagging silent false-positive `tsc --noEmit` executions on solution tsconfigs with automatic AI migration prompts and bash remediation.
  - Updated multi-stack coding standards (`CODING_STANDARDS.md`, `CODING_STANDARDS_TYPESCRIPT`) and bundled skill reference guides (`old-coder/references/gauntlet.md`) highlighting the Project References trap and full typecheck invariants.

---

## [0.5.0] - 2026-08-30

### 🚀 Added
- **Plugin Architecture & Recursive Template Scaffolding (`Task 040`)**:
  - Complete plugin template tree with full skill references under `.agents/plugins/agent-gauntlet/skills/`.
  - Authoritative reference guides bundled: `verifier.md`, `templates.md`, `gauntlet.md`, and `verifier-case-study.md` (> 200 bytes each).
  - Recursive template initialization in `agent-gauntlet init` preventing stray root `task.md` creation and standardizing on `tasks/001-bootstrap.md`.
  - Added authoritative `[paths]` manifest to `gauntlet.toml` schema and template generator.
- **Read-Only Workspace Doctor & AI Migration Scanner (`agent-gauntlet doctor`)**:
  - Read-only diagnostics inspecting missing configuration, missing skill references, truncated stubs, shadow specifications, and duplicate skills.
  - Automated generation of a copy-paste AI Migration Prompt with remediation bash scripts.
  - Seamless Node.js CLI integration in `@agent-gauntlet/cli` forwarding to Python doctor engine.

---

## [0.4.0] - 2026-08-30

### 🚀 Added
- **Local Transparent Supervisor & WASM Verifier (`Task 035`, `ADR 0007`)**:
  - Privilege-separated local background supervisor daemon evaluating capability requests outside the workspace.
  - Zero ambient authority WebAssembly policy component (`wit/gauntlet_policy.wit`) for deterministic capability evaluation.
  - Protected Key Provider managing installation identity and ephemeral task keys in `~/.agent-gauntlet/supervisor/` (`0700`/`0600`) issuing signed `LOCAL_SUPERVISED` verification reports.
  - Append-only hash-chained session event log with rolling SHA-256 root hash and tamper detection.
  - Task Session Finite State Machine (`DISCOVERED -> ACTIVE -> VERIFYING -> PASSED | FAILED | INVALIDATED -> CLOSED`).
  - Linux Platform Seam: Systemd socket activation (`agent-gauntlet.socket` & `agent-gauntlet.service` via `SD_LISTEN_FDS_START`), Unix domain socket transport, and unprivileged Bubblewrap (`bwrap`) sandbox runner for frozen workspace verification.
  - Antigravity IDE IPC Hook Shim (`features/adapters/antigravity/shim.py`) supporting `PreInvocation`, `PreToolUse`, `PostToolUse`, and `Stop` hooks with p95 < 50ms latency.
  - Offline report verifier validating `LOCAL_SUPERVISED` signatures without private keys.
- **NPM and NPX Distribution Wrapper (`Task 034`)**:
  - Published `@agent-gauntlet/cli` / `agent-gauntlet` NPM package (`packages/agent-gauntlet/`) with zero external dependencies.
  - Native Node.js CLI runner (`bin/agent-gauntlet.js`) with fail-safe Python resolution, process signal forwarding, and status/doctor diagnostics.
  - Added CLI operational subcommands: `status`, `doctor`, `uninstall`.
- **Three-Tier Evidence & Trust Boundary Model**:
  - Formally upgraded trust architecture to Three Tiers: `LOCAL_UNSUPERVISED` (fast feedback), `LOCAL_SUPERVISED` (signed local report via supervisor), and `CI_ATTESTED` (Sigstore OIDC keyless DSSE bundle).

---

## [0.3.0] - 2026-08-29

### 🚀 Added
- **Audit-Aware Release Handoff Finite State Machine (`Task 029`)**:
  - Implemented a deterministic lifecycle state machine in `infer_next_session_role()` and `is_audit_or_review_task()`.
  - Automatically transitions completed features to `Senior Software Engineer (Independent Code Review & Audit)`.
  - Automatically transitions approved audits to `Release & Operations Engineer (Release Attestation & Deployment)`.
  - Prevents review fatigue and endless AI bikeshedding loops.
- **Matt Pocock Style Two-Axis Code Review Skill (`Tasks 025, 028`)**:
  - Integrated bundled `code-review` agent skill into `.agents/skills/code-review/` and `plugins/agent-gauntlet/skills/code-review/`.
  - Implements two parallel evaluation axes: **Standards** (adherence to repository coding standards) and **Spec** (fidelity to originating requirements/tasks) with Martin Fowler code smells baseline.
- **Comprehensive Multi-Stack Coding Standards (`Tasks 026, 027`)**:
  - Authored authoritative `CODING_STANDARDS.md` covering Python (PEP 8/257, Google docstrings, type annotations), TypeScript/JavaScript (Total TypeScript, no type assertions `as`, Discriminated Unions), Rust (Clippy, error handling, safety), Go, and Modern CSS/Web.
  - Formulated core architectural guidelines: Package-by-Feature (Screaming Architecture), Fail-Closed Error Handling, Zero Silent Fallbacks, Deep Modules, and Pure Semantics in `CONTEXT.md` (Aristotle formula).
- **Role-Aware Session Handoff Prompts (`Task 024`)**:
  - Added dynamic session role inference in `infer_next_session_role()` generating tailored, copy-paste starter prompts for clean agent handoffs.

### 🔄 Changed & Refactored
- **Two-Axis Audit Remediation & Docstring Hardening (`Task 028`)**:
  - Enriched public APIs, data models, and vertical slices with comprehensive Google Docstrings (`Args:`, `Returns:`, `Raises:`).
  - Synchronized `DEFAULT_AGENTS_MD` template in `scaffolder.py` with `spec.md` governance and `🧐 CODE REVIEW / AUDIT` intent classification.
  - Added `CODING_STANDARDS.md` to `gatekeeper.py` allowed metadata paths and pruned redundant aliases.
- **Mutant Testing Gauntlet Hardening**:
  - Expanded `tools/mutants.py` suite to 46 rigorous mutations across all vertical slices with 100% kill rate (46/46 killed).

### 🛡️ Security & Assurance
- Strict adherence to **ADR 0005** Two-Tier Evidence & Trust Boundary Model.
- Zero local hardcoded secrets or signing keys; authoritative DSSE / in-toto attestations issued exclusively via privileged CI workflows with Sigstore OIDC identities.

---

## [0.2.0] - 2026-08-25

### 🚀 Added
- **Two-Tier Evidence and Trust Boundary Model (ADR 0005)**:
  - Detached in-toto / DSSE / Sigstore attestation verification via `agent-gauntlet check-attestation`.
  - Orthogonal assurance dimensions: `verification_result`, `attestation_status`, and `trust_decision`.
  - Multi-digest canonical workspace manifest with symlink boundary enforcement and SHA-256 tree hashing.
- **Two-Job CI Attestation Pipeline**:
  - Independent GitHub Actions workflow separating untrusted verification from privileged Sigstore signing.
- **Open Knowledge Files (OKF) Metadata Validation**:
  - Frontmatter schema validation for tasks, ADRs, specs, and glossaries.

---

## [0.1.0] - 2026-08-20

### 🚀 Added
- **Core Gauntlet Verification Engine**:
  - Multi-stack autodetector (Python, TypeScript, Rust, Go).
  - Fail-closed execution pipeline with configurable timeout and isolation.
- **Google Antigravity & Claude Code Adapters**:
  - Pre-tool invocation gatekeeper hooks preventing unauthorized edits and unsafe operations.
  - Task HUD cards and evidence recording.
