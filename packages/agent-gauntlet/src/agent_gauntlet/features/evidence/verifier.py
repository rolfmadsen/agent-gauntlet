"""Evidence and attestation verification execution engine."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

from agent_gauntlet.features.config.loader import load_config
from agent_gauntlet.features.diagnostics.parser import DiagnosticParser
from agent_gauntlet.features.evidence.attestation import (
    AttestationBundle,
    AttestationEngine,
)
from agent_gauntlet.features.evidence.models import (
    AttestationStatus,
    CheckSummary,
    ExecutionMetadata,
    TaskContract,
    VerificationReport,
    WorkspaceState,
)
from agent_gauntlet.features.evidence.report import VerificationReportEngine
from agent_gauntlet.features.evidence.source_state import compute_workspace_manifest
from agent_gauntlet.features.evidence.task_resolver import resolve_task_contract
from agent_gauntlet.features.evidence.trust_policy import (
    TrustPolicyEngine,
)
from agent_gauntlet.features.gauntlet.models import LayerDefinition, LayerRequirement
from agent_gauntlet.features.gauntlet.runner import run_gauntlet
from agent_gauntlet.features.okf.validator import validate_okf_workspace
from agent_gauntlet.features.tasks import parse_task_file
from agent_gauntlet.features.tasks.models import ALLOWED_ACTIVE_STATUSES, TaskStatus


def is_audit_or_review_task(task_id: str, title: str = "", content: str = "") -> bool:
    """Checks whether a task identifier, title, or content represents an audit or code review package.

    Args:
        task_id: Stem or identifier of the task file.
        title: Optional title line of the task.
        content: Optional raw markdown content of the task.

    Returns:
        True if the task is an audit or code review package, False otherwise.
    """
    task_id_lower = task_id.lower().replace("_", "-")
    title_lower = title.lower()
    content_lower = content.lower()

    if any(
        t in task_id_lower
        for t in ("audit", "code-review", "code_review", "re-review", "granskning")
    ):
        return True
    if any(
        t in title_lower for t in ("audit", "code review", "code-review", "re-review", "granskning")
    ):
        return True
    if "code-review" in content_lower or "code review" in content_lower:
        if (
            "audit" in content_lower
            or "remediation" in content_lower
            or "granskning" in content_lower
        ):
            return True
    return False


def infer_next_session_role(workspace: Path, current_task_id: str = "") -> tuple[str, str, str]:
    """Infers the next engineering role, task ID, and actionable starter prompt.

    Args:
        workspace: Path to repository workspace root.
        current_task_id: Optional task identifier being completed or verified.

    Returns:
        A tuple of (next_role, next_task_id, handoff_prompt).
    """
    tasks_dir = workspace / "tasks"
    candidate_active: tuple[str, str, str] | None = None
    candidate_draft: tuple[str, str, str] | None = None
    completed_tasks: list[tuple[str, str, str]] = []

    if tasks_dir.is_dir():
        for candidate in sorted(tasks_dir.glob("*.md")):
            try:
                raw_content = candidate.read_text(encoding="utf-8")
                task_info = parse_task_file(candidate)
                completed_tasks.append((task_info.task_id, task_info.title, raw_content))
            except Exception:
                raw_content = ""
                task_info = None

            if candidate.stem == current_task_id or candidate.name.startswith(
                f"{current_task_id}-"
            ):
                continue

            if task_info is not None:
                # Check for active task with pending work
                if task_info.status in ALLOWED_ACTIVE_STATUSES and task_info.unresolved_criteria:
                    if candidate_active is None:
                        prompt = (
                            f"Du agerer som Senior Software Engineer (Feature Implementation & Testing) på dette projekt.\n"
                            f"Din opgave er at implementere kravene i tasks/{candidate.name} i henhold til den godkendte spec.md.\n\n"
                            f"Arbejdsmetode for denne opgave:\n"
                            f"- Følg strikt Test-Driven Development (skriv og observer den første fejlede RED test før kodeændringer).\n"
                            f"- Skriv minimal produktionskode for at opnå GREEN status.\n"
                            f"- Refaktorer under frosne assertions og verificér via projektets testsuite.\n"
                            f"- Du må IKKE ændre specifikationen eller tilføje uautoriserede afhængigheder."
                        )
                        candidate_active = (
                            "Senior Software Engineer (Feature Implementation & Testing)",
                            candidate.stem,
                            prompt,
                        )
                # Check for draft task requiring specification
                elif task_info.status == TaskStatus.DRAFT or not task_info.acceptance_criteria:
                    if candidate_draft is None:
                        prompt = (
                            f"Du agerer som Senior Software Engineer (System Architecture & Requirements) på dette projekt.\n"
                            f"Din opgave er at afklare kravene til tasks/{candidate.name}, udfordre antagelser, "
                            f"definere system-invarianter (Must NOT) og formulere eksekverbare acceptkriterier i spec.md og opgavefilen, "
                            f"før kodning påbegyndes.\n"
                            f"Læs CONTEXT.md, docs/adr/ og spec.md for at sikre overensstemmelse med projektets domænemodel."
                        )
                        candidate_draft = (
                            "Senior Software Engineer (System Architecture & Requirements)",
                            candidate.stem,
                            prompt,
                        )

    if candidate_active is not None:
        return candidate_active
    if candidate_draft is not None:
        return candidate_draft

    # When all tasks are complete, determine whether an audit/code review has already been performed.
    has_audit_completed = False
    if current_task_id and is_audit_or_review_task(current_task_id):
        has_audit_completed = True
    elif completed_tasks:
        latest_task_id, latest_title, latest_content = completed_tasks[-1]
        if is_audit_or_review_task(latest_task_id, latest_title, latest_content):
            has_audit_completed = True

    if has_audit_completed:
        release_prompt = (
            "Du agerer som Release & Operations Engineer på dette projekt.\n"
            "Samtlige planlagte opgaver og uafhængige kode-granskninger (code review & audit) er gennemført og godkendt med grønt lys.\n\n"
            "Din opgave er at:\n"
            "1. Verificere release-eligibility og DSSE-attestering via 'agent-gauntlet check-attestation'.\n"
            "2. Klargøre release-dokumentation, changelog og versionsopdatering i projektkonfigurationen.\n"
            "3. Hvis der skal påbegyndes en ny epoke, definér da næste milepælsopgaver i tasks/ med udgangspunkt i ROADMAP.md."
        )
        return (
            "Release & Operations Engineer (Release Attestation & Deployment)",
            "",
            release_prompt,
        )

    # Default fallback when feature tasks are complete, but independent audit is pending
    fallback_prompt = (
        "Du agerer som Senior Software Engineer (Independent Code Review & Audit) på dette projekt.\n"
        "Alle planlagte opgaver er gennemført. Din opgave er at udføre en to-akset uafhængig granskning "
        "ved hjælp af code-review skillen (.agents/skills/code-review/SKILL.md) mod repoets standarder og spec.md "
        "for at afdække eventuelle oversete edge cases, Fowler code smells eller specifikations-afvigelser."
    )
    return (
        "Senior Software Engineer (Independent Code Review & Audit)",
        "",
        fallback_prompt,
    )


def generate_session_handoff_prompt(workspace: Path, task_id: str, task_title: str = "") -> str:
    """Generates a clean starter prompt for the next chat session using role inference.

    Args:
        workspace: Path to repository workspace root.
        task_id: Current task identifier being completed.
        task_title: Optional human-readable task title.

    Returns:
        Formatted starter prompt string for the next chat session.
    """
    _role, _next_id, prompt = infer_next_session_role(workspace, task_id)
    return prompt


def execute_verify(
    workspace: Path,
    task_id: str = "",
    stack: str = "",
    standalone: bool = False,
    test_target: str = "",
    save: bool = False,
    as_json: bool = False,
    diagnostics_json: bool = False,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Executes multi-layer gauntlet verification and builds unsigned report.

    Args:
        workspace: Path to repository workspace root.
        task_id: Optional explicit task ID to bind against.
        stack: Optional explicit stack name override.
        standalone: If True, bypasses CONTEXT.md and task criteria requirements.
        test_target: Optional dotted unit test target for targeted test run.
        save: If True, writes verification-report.json and evidence markdown files.
        as_json: If True, prints canonical verification report JSON to stdout.
        diagnostics_json: If True, prints actionable diagnostics JSON payload to stdout.
        stdout: Optional TextIO stream for standard output.
        stderr: Optional TextIO stream for standard error.

    Returns:
        Exit code: 0 if verification passes, 1 if verification or pre-flight fails.
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    start_time = time.time()
    started_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest_pre = compute_workspace_manifest(workspace)
    config = load_config(workspace, explicit_stack=stack or None)

    resolved_task_id, task_title, criteria, unresolved = resolve_task_contract(workspace, task_id)

    if not standalone and not test_target:
        context_file = workspace / "CONTEXT.md"
        if not context_file.exists() or not context_file.read_text(encoding="utf-8").strip():
            print(
                "FAILED: Pre-flight check failed! CONTEXT.md is missing or empty. Please define domain glossary in CONTEXT.md or use --standalone.",
                file=err,
            )
            return 1

        okf_report = validate_okf_workspace(workspace)
        if not okf_report.valid:
            print(
                f"FAILED: Pre-flight OKF validation failed! {len(okf_report.findings)} documentation defect(s) found:",
                file=err,
            )
            for f in okf_report.findings[:5]:
                try:
                    rel_p = Path(f.file_path).relative_to(workspace)
                except ValueError:
                    rel_p = f.file_path
                print(f"  [!] {f.rule} in {rel_p}: {f.message}", file=err)
                if f.remediation_hint:
                    print(f"      Hint: {f.remediation_hint}", file=err)
            if len(okf_report.findings) > 5:
                print(
                    f"  ... and {len(okf_report.findings) - 5} more defect(s). Run 'agent-gauntlet okf validate' for full report.",
                    file=err,
                )
            return 1

    layers: list[LayerDefinition] = []
    if test_target:
        layers.append(
            LayerDefinition(
                name="targeted-test",
                command=[sys.executable, "-m", "unittest", test_target],
                optional=False,
            )
        )
    else:
        layers = config.to_layer_definitions()

    report = run_gauntlet(layers, cwd=workspace)
    finished_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    total_duration = time.time() - start_time
    manifest_post = compute_workspace_manifest(workspace)

    diagnostic_parser = DiagnosticParser()
    diagnostic_reports = [
        diagnostic_parser.parse_layer_output(
            layer_name=res.name,
            command=layers[i].command if i < len(layers) else [res.name],
            exit_code=res.exit_code,
            output=res.output,
        )
        for i, res in enumerate(report.layers)
    ]

    checks = [
        CheckSummary(
            name=layer.name,
            status="PASSED" if layer.passed else "FAILED",
            passed=layer.passed,
            exit_code=layer.exit_code,
            duration_seconds=layer.duration_seconds,
            optional=(layer.requirement == LayerRequirement.OPTIONAL),
            log_digest=hashlib.sha256(layer.output.encode("utf-8")).hexdigest()
            if layer.output
            else "",
        )
        for layer in report.layers
    ]

    check_defs_hasher = hashlib.sha256()
    for layer_def in layers:
        cmd_str = " ".join(layer_def.command)
        check_defs_hasher.update(
            f"{layer_def.name}:{cmd_str}:{layer_def.optional}\n".encode("utf-8")
        )
    check_definitions_digest = check_defs_hasher.hexdigest()

    task_contract = TaskContract(
        task_id=resolved_task_id,
        task_title=task_title,
        task_digest=manifest_post.task_digest,
        acceptance_criteria=criteria,
        unresolved_criteria=unresolved,
    )

    workspace_state = WorkspaceState(
        manifest_version="1.0",
        source_content_digest=manifest_post.source_content_digest,
        source_manifest_digest_pre=manifest_pre.source_manifest_digest,
        source_manifest_digest_post=manifest_post.source_manifest_digest,
        config_digest=manifest_post.config_digest,
        task_digest=manifest_post.task_digest,
        policy_digest=manifest_post.policy_digest,
        check_definitions_digest=check_definitions_digest,
        included_files_count=manifest_post.included_files_count,
        vcs=manifest_post.vcs,
    )

    exec_metadata = ExecutionMetadata(
        started_at=started_iso,
        finished_at=finished_iso,
        total_duration_seconds=total_duration,
        environment={
            "python_version": sys.version.split()[0],
            "platform": sys.platform,
            "gauntlet_version": "0.3.0",
        },
    )

    has_mandatory_failures = any(not c.passed or c.exit_code != 0 for c in checks if not c.optional)
    has_optional_failures = any(not c.passed or c.exit_code != 0 for c in checks if c.optional)
    is_self_mutated = manifest_pre.source_manifest_digest != manifest_post.source_manifest_digest

    # Invariant: Must have non-empty checks and non-empty criteria to pass
    if is_self_mutated:
        verdict = "FAILED"
    elif not report.success or has_mandatory_failures:
        verdict = "FAILED"
    elif test_target:
        verdict = "PARTIAL"
    elif not criteria and not standalone:
        verdict = "INCOMPLETE"
    elif not checks:
        verdict = "FAILED"
    elif unresolved:
        verdict = "INCOMPLETE"
    elif has_optional_failures:
        verdict = "PARTIAL"
    else:
        verdict = "PASSED"

    all_diagnostic_findings = [f.to_dict() for r in diagnostic_reports for f in r.findings]

    report_obj = VerificationReport(
        schema_version="2.0.0",
        execution_origin="LOCAL",
        verdict=verdict,
        task_contract=task_contract,
        workspace_state=workspace_state,
        execution_metadata=exec_metadata,
        checks=checks,
        diagnostics=all_diagnostic_findings,
    )

    engine = VerificationReportEngine()
    if save:
        report_json_str = engine.generate_report_json(report_obj)
        (workspace / "verification-report.json").write_text(report_json_str, encoding="utf-8")
        (workspace / config.evidence_file).write_text(report_json_str, encoding="utf-8")
        (workspace / config.evidence_markdown_file).write_text(
            engine.generate_report_markdown(report_obj), encoding="utf-8"
        )

    next_role, next_task_id, handoff_prompt = (
        infer_next_session_role(
            workspace,
            report_obj.task_contract.task_id,
        )
        if verdict == "PASSED"
        else ("", "", "")
    )

    tree_digest = manifest_post.source_manifest_digest[:16]
    if test_target:
        # Targeted developer test runs are advisory and succeed if target tests passed
        is_verify_success = report.success
    else:
        # Full gauntlet verification strictly requires full PASSED verdict
        is_verify_success = verdict == "PASSED"

    if diagnostics_json:
        output_payload = {
            "verdict": verdict,
            "source_tree_hash": tree_digest,
            "execution_origin": "LOCAL",
            "diagnostic_reports": [r.to_dict() for r in diagnostic_reports],
            "next_role": next_role,
            "handoff_prompt": handoff_prompt,
        }
        print(json.dumps(output_payload, indent=2), file=out)
    elif as_json:
        print(engine.generate_report_json(report_obj), file=out)
    else:
        print(f"\nVerification Result: {verdict}", file=out)
        if report_obj.task_contract.task_id and report_obj.task_contract.task_id != "default-run":
            task_label = (
                f"{report_obj.task_contract.task_id} ({report_obj.task_contract.task_title})"
                if report_obj.task_contract.task_title
                else report_obj.task_contract.task_id
            )
            print(f"Bound Task:          {task_label}", file=out)
        print(f"Stack Profile:       {config.stack}", file=out)
        print(f"Source Tree Hash:    {tree_digest}", file=out)
        print("Execution Origin:    LOCAL (Unsigned report)", file=out)
        print("\nVerification Layers:", file=out)
        for c in report_obj.checks:
            tag = "[+]" if c.passed else "[-]"
            print(f"  {tag} {c.name} (exit {c.exit_code}) in {c.duration_seconds:.3f}s", file=out)

        all_findings = [f for r in diagnostic_reports for f in r.findings]
        if all_findings:
            print("\nActionable Diagnostics:", file=out)
            for f in all_findings:
                location = (
                    f"{f.file_path}:{f.line_number}"
                    if f.file_path and f.line_number
                    else (f.file_path or f.tool_name)
                )
                print(f"  [!] {f.finding_type.value} in {location}", file=out)
                print(f"      Message: {f.message}", file=out)
                if f.remediation_hint:
                    print(f"      Hint:    {f.remediation_hint}", file=out)

        for l_res in report.layers:
            if not l_res.passed and l_res.output:
                print(
                    f"\n[!] Layer '{l_res.name}' Execution Logs:\n{l_res.output.strip()}", file=err
                )

        if verdict == "PASSED" and handoff_prompt:
            import textwrap

            print("\n" + "╭" + "─" * 76 + "╮", file=out)
            print(f"│ 🏁 SESSION HANDOFF: {report_obj.task_contract.task_id:<53} │", file=out)
            if next_role:
                print(f"│ 👤 Næste Rolle: {next_role:<58} │", file=out)
            print("│" + " " * 76 + "│", file=out)
            print(
                "│ 💡 Start venligst en frisk chat-session for at undgå context rot.          │",
                file=out,
            )
            print(
                "│ 📋 Kopiér og indsæt følgende starter-prompt i en ny chat:                  │",
                file=out,
            )
            print("├" + "─" * 76 + "┤", file=out)
            for paragraph in handoff_prompt.splitlines():
                if not paragraph.strip():
                    print("│" + " " * 76 + "│", file=out)
                    continue
                for wrapped_line in textwrap.wrap(paragraph, width=74):
                    print(f"│ {wrapped_line:<74} │", file=out)
            print("╰" + "─" * 76 + "╯", file=out)

    return 0 if is_verify_success else 1


def execute_check_evidence(
    workspace: Path,
    evidence_file: str = "",
    legacy_advisory: bool = False,
    as_json: bool = False,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Checks verification report integrity, criteria resolution, check outcomes, and workspace state.

    Args:
        workspace: Path to repository workspace root.
        evidence_file: Optional path or filename for verification-report.json.
        legacy_advisory: If True, inspects legacy v1 evidence payloads in non-blocking advisory mode.
        as_json: If True, prints status payload JSON to stdout.
        stdout: Optional TextIO stream for standard output.
        stderr: Optional TextIO stream for standard error.

    Returns:
        Exit code: 0 if evidence matches current workspace state and all criteria/checks passed, 1 on failure.
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    engine = VerificationReportEngine()
    target_file = evidence_file
    if not target_file:
        if (workspace / "verification-report.json").is_file():
            target_file = "verification-report.json"
        elif (workspace / "evidence.json").is_file():
            target_file = "evidence.json"
        else:
            target_file = "verification-report.json"

    evidence_path = (
        workspace / target_file if not Path(target_file).is_absolute() else Path(target_file)
    )
    if not evidence_path.is_file():
        print(f"FAILED: Evidence file '{evidence_path}' does not exist.", file=err)
        return 1

    try:
        raw_content = evidence_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"FAILED: Failed to parse evidence file '{evidence_path}': {exc}", file=err)
        return 1

    classification = engine.classify_evidence_payload(raw_content)
    if classification == "LEGACY_UNATTESTED":
        if not legacy_advisory:
            print(
                "FAILED: Legacy v1 HMAC evidence detected. Legacy evidence cannot satisfy authoritative verification gates. "
                "Re-run 'agent-gauntlet verify' to produce an unsigned v2 verification report, or pass --legacy-advisory for local advisory inspection.",
                file=err,
            )
            return 1
        else:
            print(
                f"[LEGACY_UNATTESTED] Legacy evidence in '{evidence_path}' inspected in advisory mode.",
                file=out,
            )
            return 0

    try:
        report_obj = engine.load_report_json(raw_content)
    except Exception as exc:
        print(f"FAILED: Failed to parse verification report '{evidence_path}': {exc}", file=err)
        return 1

    if report_obj.verdict != "PASSED":
        print(
            f"FAILED: Verification report records non-passed verdict: '{report_obj.verdict}'.",
            file=err,
        )
        return 1

    # Invariant: Non-empty criteria required for PASSED verification
    if not report_obj.task_contract.acceptance_criteria:
        print("FAILED: Verification report has 0 acceptance criteria.", file=err)
        return 1

    if report_obj.task_contract.unresolved_criteria:
        print(
            f"FAILED: Verification report has {len(report_obj.task_contract.unresolved_criteria)} unresolved acceptance criteria.",
            file=err,
        )
        return 1

    # Invariant: Non-empty checks required
    if not report_obj.checks:
        print("FAILED: Verification report contains 0 verification checks.", file=err)
        return 1

    failed_checks = [
        c
        for c in report_obj.checks
        if not c.optional and (not c.passed or c.exit_code != 0 or c.status == "FAILED")
    ]
    if failed_checks:
        print(
            f"FAILED: Verification report contains {len(failed_checks)} failed check(s): {[c.name for c in failed_checks]}.",
            file=err,
        )
        return 1

    current_manifest = compute_workspace_manifest(workspace)
    if not engine.verify_workspace_state_match(
        report_obj,
        current_manifest.source_manifest_digest,
        current_manifest.policy_digest,
        current_manifest.config_digest,
        current_manifest.task_digest,
    ):
        report_digest = report_obj.workspace_state.source_manifest_digest_post or "(none)"
        print(
            f"FAILED: Source manifest, policy, config, or task drift detected! Report bound to '{report_digest}', current workspace manifest is '{current_manifest.source_manifest_digest}'.",
            file=err,
        )
        return 1

    if as_json:
        print(
            json.dumps(
                {"status": "VALID", "report": json.loads(engine.generate_report_json(report_obj))},
                indent=2,
            ),
            file=out,
        )
    else:
        print(
            f"[VALID] Source manifest verified ({current_manifest.source_manifest_digest[:16]}) [origin: {report_obj.execution_origin}, attestation: ABSENT].",
            file=out,
        )
    return 0


def execute_check_attestation(
    workspace: Path,
    report_file: str,
    attestation_file: str = "",
    policy_file: str = "",
    allow_unattested: bool = False,
    as_json: bool = False,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Checks verification report and cryptographic DSSE attestation against consumer TrustPolicy.

    Args:
        workspace: Path to repository workspace root.
        report_file: Path to verification-report.json.
        attestation_file: Optional path to attestation.json / bundle.
        policy_file: Optional path to trust-policy.json.
        allow_unattested: If True, permits unattested verification reports when attestation is absent.
        as_json: If True, outputs trust evaluation result JSON to stdout.
        stdout: Optional TextIO stream for standard output.
        stderr: Optional TextIO stream for standard error.

    Returns:
        Exit code: 0 if release eligible or permitted, 1 on failure or denial.
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    report_path = Path(report_file)
    if not report_path.is_absolute():
        report_path = (workspace / report_path).resolve()

    if not report_path.is_file():
        print(f"FAILED: Verification report '{report_path}' not found.", file=err)
        return 1

    raw_report = report_path.read_text(encoding="utf-8")
    report_engine = VerificationReportEngine()
    try:
        report_obj = report_engine.load_report_json(raw_report)
    except Exception as exc:
        print(f"FAILED: Failed to parse verification report '{report_path}': {exc}", file=err)
        return 1

    # Invariants: Non-empty criteria and non-empty checks
    if not report_obj.task_contract.acceptance_criteria:
        print("FAILED: Verification report has 0 acceptance criteria.", file=err)
        return 1

    if not report_obj.checks:
        print("FAILED: Verification report contains 0 verification checks.", file=err)
        return 1

    current_manifest = compute_workspace_manifest(workspace)
    if not report_engine.verify_workspace_state_match(
        report_obj,
        current_manifest.source_manifest_digest,
        current_manifest.policy_digest,
        current_manifest.config_digest,
        current_manifest.task_digest,
    ):
        report_digest = report_obj.workspace_state.source_manifest_digest_post or "(none)"
        print(
            f"FAILED: Source manifest, policy, config, or task drift detected! Report bound to '{report_digest}', current workspace manifest is '{current_manifest.source_manifest_digest}'.",
            file=err,
        )
        return 1

    # Load Attestation bundle if provided / present
    attestation_bundle: AttestationBundle | None = None
    attestation_engine = AttestationEngine()
    attestation_path_str = attestation_file
    if not attestation_path_str and (workspace / "attestation.json").is_file():
        attestation_path_str = str(workspace / "attestation.json")

    if attestation_path_str:
        att_path = Path(attestation_path_str)
        if not att_path.is_absolute():
            att_path = (workspace / att_path).resolve()
        if att_path.is_file():
            raw_bundle = att_path.read_text(encoding="utf-8")
            bundle = attestation_engine.load_bundle(raw_bundle)
            status = attestation_engine.verify_bundle_against_report(bundle, raw_report)
            if status != AttestationStatus.VALID:
                attestation_bundle = AttestationBundle(
                    bundle_version=bundle.bundle_version,
                    status=AttestationStatus.INVALID,
                    identity=bundle.identity,
                    subject_digest=bundle.subject_digest,
                )
            else:
                attestation_bundle = bundle

    # Load TrustPolicy
    trust_engine = TrustPolicyEngine()
    policy_path_str = policy_file
    if not policy_path_str and (workspace / ".agent-gauntlet/trust-policy.json").is_file():
        policy_path_str = str(workspace / ".agent-gauntlet/trust-policy.json")

    if policy_path_str:
        p_path = Path(policy_path_str)
        if not p_path.is_absolute():
            p_path = (workspace / p_path).resolve()
        trust_policy = trust_engine.load_policy(p_path)
    else:
        trust_policy = trust_engine.load_policy({})

    evaluation_result = trust_engine.evaluate(
        report=report_obj,
        attestation=attestation_bundle,
        policy=trust_policy,
    )

    attestation_status_val = (
        attestation_bundle.status.value if attestation_bundle else AttestationStatus.ABSENT.value
    )
    verification_result_val = report_obj.verdict
    trust_decision_val = evaluation_result.trust_decision.value
    release_eligible = evaluation_result.release_eligible

    if allow_unattested and attestation_status_val == AttestationStatus.ABSENT.value:
        is_success = (
            report_obj.verdict == "PASSED" and not report_obj.task_contract.unresolved_criteria
        )
    else:
        is_success = release_eligible

    if as_json:
        result_payload = {
            "verification_result": verification_result_val,
            "attestation_status": attestation_status_val,
            "trust_decision": trust_decision_val,
            "release_eligible": release_eligible,
            "reasons": evaluation_result.reasons,
            "subject_digest": evaluation_result.evaluated_subject,
            "issuer": evaluation_result.evaluated_issuer,
        }
        print(json.dumps(result_payload, indent=2), file=out)
    else:
        print("\nAttestation & Trust Evaluation:", file=out)
        print(f"  Verification Result:  {verification_result_val}", file=out)
        print(f"  Attestation Status:   {attestation_status_val}", file=out)
        print(f"  Trust Decision:       {trust_decision_val}", file=out)
        print(f"  Release Eligible:     {'YES' if release_eligible else 'NO'}", file=out)
        if evaluation_result.reasons:
            print("\nEvaluation Details / Reasons:", file=out)
            for r in evaluation_result.reasons:
                print(f"  [!] {r}", file=err if not is_success else out)

    return 0 if is_success else 1
