---
type: Architectural Decision Record
title: 'ADR 0006: Multi-Harness Policy Adapter Contract and Trusted Context'
status: draft
tags:
- architecture
- adr
- security
- adapters
- okf
generated:
  by: antigravity/gemini-3.7-flash
  at: '2026-08-25T15:39:00Z'
verified: []
---

# 6. Multi-Harness Policy Adapter Contract and Trusted Context

**Status**: `accepted` (Extends ADR 0004)  
**Date**: `2026-08-25`

## Context
ADR 0004 established vertical adapter slices for agent harnesses. However, the initial implementation allowed untrusted caller payloads to pass authority-defining parameters directly into gatekeeper logic, used flat dictionaries with nullable fields, and failed open on corrupted input streams.

## Decision
1. **Explicit Separation of Request vs Trusted Context**:
   The policy evaluation contract is strictly defined as:
   ```python
   PolicyEngine.evaluate(
       request: CapabilityRequest,
       context: TrustedEnforcementContext,
   ) -> PolicyDecision
   ```
   - `CapabilityRequest` is a discriminated union of typed requests (`ExecuteCommandRequest`, `WriteFileRequest`, `ReadFileRequest`, `UnknownToolRequest`).
   - `TrustedEnforcementContext` is constructed exclusively by `agent-gauntlet` from trusted runtime inspection (resolved canonical workspace path, active task status discovered from `tasks/`, read-only flags, and immutable allowed metadata paths). Adapters cannot override context parameters from raw tool arguments.

2. **Harness-Specific Fail-Closed Enforcement**:
   All adapter entrypoints and hook parsers MUST fail closed according to their platform's specific hook contract:
   - For Google Antigravity: Emit stdout `{"decision": "deny", "reason": "..."}` AND return exit code 1.
   - Corrupted, empty, or unparseable input streams fail closed immediately.

3. **Zero Cryptographic Authority**:
   Adapters are strictly transport-layer translators. They MUST NOT manage cryptographic keys, issue signatures, or alter verification reports.

4. **Shared Conformance Test Suite**:
   Every harness adapter must pass a parameterized conformance test suite validating typed request translation, fail-closed handling of malformed payloads, and immutability of the trusted context.

## Consequences
- Prevents malicious or confused-deputy agents from bypassing path or command restrictions by manipulating hook payloads.
- Ensures all harness implementations adhere to identical security invariants.
