# Changelog

All notable changes to the `agent-gauntlet` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
