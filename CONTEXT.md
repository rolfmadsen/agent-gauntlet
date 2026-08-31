---
type: Knowledge Bundle Index
title: "agent-gauntlet Context & Domain Glossary"
description: "Kernebegreber, arkitekturgrænser og definitioner for agent-gauntlet"
status: stable
generated: { by: antigravity/gemini-3.7-flash, at: 2026-08-30T09:18:00Z }
tags: [glossary, domain-model, ubiquitous-language, okf, supervisor, wasm]
---

# agent-gauntlet Context & Domain Glossary

This document defines the core ubiquitous language for `agent-gauntlet` using Aristotle's formula (*definitio per genus et differentiam*). It captures domain concepts without implementation noise.

---

## 📖 Core Concepts

**Task**:
An executable unit of engineering work, that has bounded acceptance criteria and verifiable completion evidence.
_Avoid_: Ticket, issue, story, workitem.

**Layer**:
A verification step, that executes a specific analysis or testing command within a bounded timeout.
_Avoid_: Stage, phase, check-item.

**Gauntlet**:
A sequential verification pipeline, that executes verification layers with fail-closed semantics and halts on the first mandatory failure.
_Avoid_: Test runner, CI script, harness.

**Three-Tier Trust Boundary**:
A derived classification model, that categorizes verification records across three progressive trust boundaries: local unsupervised (`LOCAL_UNSUPERVISED`), privilege-separated supervised (`LOCAL_SUPERVISED`), and cryptographically attested (`CI_ATTESTED`).
_Avoid_: Security level, verification stage, permission rank.

**Supervisor**:
A privilege-separated background daemon, that evaluates agent capabilities, manages task session lifecycles, and signs local verification reports outside the workspace boundary.
_Avoid_: Background process, helper daemon, root runner.

**Supervisor State Machine**:
A deterministic finite-state machine, that governs the lifecycle, execution leases, and verification states of a supervisor session across valid transitions (`UNINITIALIZED`, `IDLE`, `TASK_ACTIVE`, `VERIFYING`, `EVICTED`, `TERMINATED`).
_Avoid_: Daemon state, session status, process loop.

**WASM Policy Component**:
A zero-authority WebAssembly binary, that deterministically evaluates capability requests against an immutable enforcement context without access to ambient system resources.
_Avoid_: Wasm sandbox, plugin module, custom script.

**Execution Lease**:
A cryptographically bounded authorization window, that grants an agent time-limited permissions to execute protected tools under an active task.
_Avoid_: Time-to-live token, session duration, execution timeout.

**Task Certificate**:
A cryptographically signed token, that binds ephemeral task keys and session parameters to the persistent installation identity.
_Avoid_: Session token, API key, auth bearer.

**Supervised Evidence Receipt**:
A locally signed verification artifact, that cryptographically binds execution outcomes to the supervisor's hardware- or OS-backed ephemeral identity.
_Avoid_: Local signature, HMAC tag, proof token.

**Platform Seam**:
An isolated abstraction boundary, that encapsulates operating-system-specific services, IPC transports, sandboxes, and key stores behind pure interfaces.
_Avoid_: Platform manager, OS wrapper, compatibility layer.

**Socket Activation**:
An operating system mechanism, that spawns or connects daemon services on-demand when IPC socket connections arrive.
_Avoid_: Auto-restart, background daemon loop, polling service.

**Diagnostic Finding**:
A structured defect model, that pinpoints an exact file location, error category, message, and actionable remediation hint.
_Avoid_: Error log, raw stderr, traceback.

**Diagnostic Report**:
A consolidated finding summary, that groups diagnostic findings per executed layer.
_Avoid_: Test result, summary log.

**Stack Profile**:
A preconfigured collection of verification layers, that matches the conventions and toolchains of a specific programming language.
_Avoid_: Environment, runtime config.

**Canonical Workspace Manifest**:
A deterministic SHA-256 digest, that captures normalized file contents, executable modes, and verified symlink boundaries across in-scope workspace paths.
_Avoid_: Git commit, workspace hash, checksum.

**Verification Report**:
An unsigned data record, that binds verification layer outcomes, diagnostic findings, and task contracts to the workspace manifest digests.
_Avoid_: Proof report, receipt, certification.

**Attestation Bundle**:
A detached cryptographic statement, that binds an authenticated, independent CI identity to verification reports and source digests via keyless OIDC and DSSE/in-toto envelopes.
_Avoid_: Local signature, HMAC receipt, inline certificate.

**Architecture Decision Record (ADR)**:
An immutable decision record, that captures an architectural choice, its context, and consequences.
_Avoid_: Design doc, spec document, meeting notes.

**Source Drift**:
A state discrepancy, where the current workspace source tree hash no longer matches the source tree hash bound in the evidence record.
_Avoid_: Code drift, stale build, dirty working tree.

**Harness Adapter**:
An autonomous vertical feature slice, that translates platform-specific agent events, tool calls, and manifests into canonical gauntlet operations.
_Avoid_: Plugin bridge, wrapper script, foreign hook.

**Capability Request**:
A strongly-typed operation descriptor, that represents an agent action before policy evaluation.
_Avoid_: Raw tool payload, json argument, command invocation.

**Trusted Enforcement Context**:
An immutable runtime descriptor, that defines workspace boundaries, active task authority, and security policies independently of caller input.
_Avoid_: Hook arguments, ambient context, caller state.

**Plugin Manifest**:
A declarative metadata ledger, that defines an adapter plugin's exposed skills, hooks, and verified entrypoints.
_Avoid_: Config file, package descriptor, json header.

**Open Knowledge Format (OKF)**:
A vendor-neutral knowledge specification, that defines Markdown document metadata, provenance, trust tiers, and lifecycle signals via YAML frontmatter.
_Avoid_: Custom header, config comment, doc schema.

**Trust Tier**:
A derived credibility classification, that categorizes a document's verification state (`unverified`, `machine-confirmed`, `human-reviewed`) based on its `verified` metadata.
_Avoid_: Approval score, rating, trust flag.

**Attested Computation**:
A standalone execution contract, that binds an explicit runtime and deterministic attester to computational output receipts.
_Avoid_: Verification script, runner config, calculation function.

**Release Readiness Gate**:
A pre-flight verification contract, that evaluates version harmony across project manifests, changelog synchronization, and architecture decision record coverage prior to software publication.
_Avoid_: Release check, version linter, publication script.

**Composite Coding Standards**:
A unified guidelines document, that combines language-specific conventions and transversal engineering invariants across multiple programming stacks within a polyglot workspace.
_Avoid_: Merged docs, mixed styleguide, combined rules.

