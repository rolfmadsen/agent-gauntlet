---
type: Knowledge Bundle Index
title: "agent-gauntlet Context & Domain Glossary"
description: "Kernebegreber, arkitekturgrænser og definitioner for agent-gauntlet"
status: stable
generated: { by: antigravity/gemini-3.7-flash, at: 2026-08-23T13:25:00Z }
tags: [glossary, domain-model, ubiquitous-language, okf]
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

**Diagnostic Finding**:
A structured defect model, that pinpoints an exact file location, error category, message, and actionable remediation hint.
_Avoid_: Error log, raw stderr, traceback.

**Diagnostic Report**:
A consolidated finding summary, that groups diagnostic findings per executed layer.
_Avoid_: Test result, summary log.

**Stack Profile**:
A preconfigured collection of verification layers, that matches the conventions and toolchains of a specific programming language.
_Avoid_: Environment, runtime config.

**Source Tree Hash**:
A deterministic SHA-256 digest, that captures the exact content state of all tracked source files in a workspace.
_Avoid_: Git commit, workspace hash, checksum.

**Evidence Record**:
An immutable cryptographic ledger, that binds a task's verification outcome to the workspace's source tree hash via HMAC-SHA256.
_Avoid_: Proof report, receipt, certification.

**Architecture Decision Record (ADR)**:
An immutable decision record, that captures an architectural choice, its context, and consequences.
_Avoid_: Design doc, spec document, meeting notes.

**Source Drift**:
A state discrepancy, where the current workspace source tree hash no longer matches the source tree hash bound in the evidence record.
_Avoid_: Code drift, stale build, dirty working tree.

**Harness Adapter**:
An autonomous vertical feature slice, that translates platform-specific agent events, tool calls, and manifests into canonical gauntlet operations.
_Avoid_: Plugin bridge, wrapper script, foreign hook.

**Normalized Tool Call**:
A canonical representation of an agent action, that categorizes tool executions into deterministic operations (file edit, shell execution, read-only).
_Avoid_: Raw tool payload, json argument, command invocation.

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

